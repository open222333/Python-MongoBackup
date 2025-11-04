from argparse import ArgumentParser
from src import MONGO_INFO, OUTPUT_DIR, LOG_LEVEL, LOG_FILE_DISABLE
from src.mongo import MongoTool, MongoMappingCollections, MongoToolSSH
from src.tool import parse_db_collections, print_config, wait_for_user_confirmation
from src.logger import Log
import textwrap
import socket
import json
import os

'''
備份-還原 範本

根據 conf/mongo.json 執行
'''


parser = ArgumentParser(description='批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行')
json_path = parser.add_argument(
    '-j', '--json_path', default=None,
    help='json檔路徑, 預設 ./conf/mongo.json\nJSON 設定檔路徑，請依照以下格式：\n' + textwrap.dedent(
        """
              {
                "execute": true,
                "ssh": {
                    "enable": true,
                    "host": "remote_host_ip_or_domain",
                    "port": 22,
                    "username": "ssh_user",
                    "password": "ssh_password",
                    "key_path": "/path/to/private_key",
                    "use_key": false
                },
                "action": {
                  "dump": {
                    "host": "127.0.0.1",
                    "port": "27017",
                    "username": "your_user",
                    "password": "your_pass",
                    "items": [
                      {
                        "database": "your_db",
                        "collections": ["col1", "col2"]
                      }
                    ]
                  },
                  "restore": {
                    "drop_collection": true,
                    "date": "20240508",
                    "attach_date": true,
                    "items": [
                      {
                        "database": "your_db",
                        "dirpath": "/path/to/backup"
                      }
                    ]
                  }
                }
              }
            ]
        """
    ))
args = parser.parse_args()

backup_logger = Log('BACKUP')
if LOG_LEVEL:
    backup_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    backup_logger.set_date_handler()
backup_logger.set_msg_handler()

if args.json_path != None:
    if os.path.exists(args.json_path):
        backup_logger.info(f'使用 json_path: {args.json_path}')
        with open(args.json_path, 'r') as f:
            MONGO_INFO = json.loads(f.read())

if __name__ == "__main__":

    print_config(MONGO_INFO)
    wait_for_user_confirmation()

    for info in MONGO_INFO:
        if not info.get('execute'):
            continue

        ssh_info = info.get('ssh', {})
        use_ssh = ssh_info.get('enable', False)

        # SSH 設定（如有）
        ssh_params = {}
        if use_ssh:
            ssh_params = dict(
                ssh_host=ssh_info.get('host'),
                ssh_port=ssh_info.get('port', 22),
                ssh_user=ssh_info.get('username'),
                ssh_password=ssh_info.get('password'),
                ssh_key_path=ssh_info.get('key_path'),
                use_key=ssh_info.get('use_key', False)
            )

        # === 匯出 ===
        if info['action'].get('dump'):
            backup_logger.info('執行匯出')
            dump_info = info['action']['dump']

            host = dump_info.get('host', '127.0.0.1')
            port = dump_info.get('port', '27017')
            username = dump_info.get('username')
            password = dump_info.get('password')
            hostname = dump_info.get('hostname', socket.gethostname())

            for item in dump_info['items']:
                database = item['database']
                collections = item.get('collections', [])

                # 若沒指定 collections 則預設全部
                if len(collections) == 0:
                    backup_logger.info(f'匯出資料庫: {database}，集合: {collections}')
                    mmc = MongoMappingCollections(f'{host}:{port}')
                    mmc.set_databases(database)
                    collections = mmc.get_all_collections()[database]

                for collection in collections:
                    backup_logger.info(f'匯出資料庫: {database}，集合: {collection}')
                    if use_ssh:
                        mt = MongoToolSSH(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname),
                            **ssh_params
                        )
                    else:
                        mt = MongoTool(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )

                    if username and password:
                        mt.set_auth(username, password)

                    mt.dump()

                    if use_ssh:
                        mt.close_ssh()

        # === 匯入 ===
        if info['action'].get('restore'):
            backup_logger.info('執行匯入')
            restore_info = info['action']['restore']

            host = restore_info.get('host', '127.0.0.1')
            port = restore_info.get('port', '27017')
            username = restore_info.get('username')
            password = restore_info.get('password')
            hostname = restore_info.get('hostname', socket.gethostname())

            for item in restore_info['items']:
                database = item['database']
                collections = item.get('collections', [])

                if len(collections) == 0:
                    if item.get('dirpath'):
                        collections = parse_db_collections(item.get('dirpath'))[database]
                        backup_logger.info(f'匯入資料庫: {database}，集合: {collections}')
                    else:
                        continue

                for collection in collections:
                    backup_logger.info(f'匯入資料庫: {database}，集合: {collection}')

                    if use_ssh:
                        mt = MongoToolSSH(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname),
                            **ssh_params
                        )
                    else:
                        mt = MongoTool(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )

                    if username and password:
                        mt.set_auth(username, password)

                    # 是否刪除集合
                    if restore_info.get('drop_collection'):
                        backup_logger.info(f'刪除集合: {collection}')
                        mt.drop_collection()

                    # 指定日期
                    if restore_info.get('date'):
                        backup_logger.info(f'指定日期: {restore_info["date"]}')
                        mt.set_date(date=restore_info['date'])

                    # 集合名稱是否附加日期
                    if restore_info.get('attach_date'):
                        backup_logger.info('集合名稱不帶日期')
                        mt.restore(name=f'{collection}_{mt.date}')
                    else:
                        mt.restore()

                    # 清空集合
                    if restore_info.get('clear_doc'):
                        backup_logger.info(f'清空集合資料: {collection}')
                        mt.delete_all_document()

                    if use_ssh:
                        mt.close_ssh()

    backup_logger.info('備份還原完成')
