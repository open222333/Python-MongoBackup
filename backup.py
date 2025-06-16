from argparse import ArgumentParser
from src import MONGO_INFO, OUTPUT_DIR, LOG_LEVEL, LOG_FILE_DISABLE
from src.mongo import MongoTool, MongoMappingCollections
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
json_path = parser.add_argument('-j', '--json_path', default=None,
        help='json檔路徑, 預設 ./conf/mongo.json\nJSON 設定檔路徑，請依照以下格式：\n' + textwrap.dedent("""
            [
              {
                "execute": true,
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
        """)
    )
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
        if info.get('execute'):

            # 執行匯出
            if info['action'].get('dump'):
                backup_logger.info('執行匯出')
                host = info['action']['dump'].get('host')
                if host == None:
                    host = '127.0.0.1'

                port = info['action']['dump'].get('port')
                if port == None:
                    port = '27017'

                username = info['action']['dump'].get('username')
                password = info['action']['dump'].get('password')

                hostname = info['action']['dump'].get('hostname')
                if hostname == None:
                    hostname = socket.gethostname()

                for item in info['action']['dump']['items']:
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
                        mt = MongoTool(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )
                        if username and password:
                            mt.set_auth(username, password)
                        mt.dump()

            # 執行匯入
            if info['action'].get('restore'):

                backup_logger.info('執行匯入')
                host = info['action']['restore'].get('host')
                if host == None:
                    host = '127.0.0.1'

                port = info['action']['restore'].get('port')
                if port == None:
                    port = '27017'

                username = info['action']['restore'].get('username')
                password = info['action']['restore'].get('password')

                hostname = info['action']['restore'].get('hostname')
                if hostname == None:
                    hostname = socket.gethostname()

                for item in info['action']['restore']['items']:
                    database = item['database']
                    collections = item.get('collections', [])

                    if len(collections) == 0:
                        if item.get('dirpath'):
                            # 取得資料夾內的集合
                            collections = parse_db_collections(item.get('dirpath'))[database]
                            backup_logger.info(f'匯入資料庫: {database}，集合: {collections}')
                        else:
                            continue

                    for collection in collections:
                        backup_logger.info(f'匯入資料庫: {database}，集合: {collection}')
                        mt = MongoTool(
                            host=f'{host}:{port}',
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )

                        if username and password:
                            mt.set_auth(username, password)

                        # 刪除目前的集合
                        if info['action']['restore'].get('drop_collection'):
                            backup_logger.info(f'刪除集合: {collection}')
                            mt.drop_collection()

                        # 指定日期
                        if info['action']['restore'].get('date'):
                            backup_logger.info(f'指定日期: {info["action"]["restore"]["date"]}')
                            mt.set_date(date=info['action']['restore']['date'])

                        # 集合名稱不帶日期
                        if info['action']['restore'].get('attach_date'):
                            backup_logger.info(f'集合名稱不帶日期')
                            mt.restore(name=f'{collection}_{mt.date}')
                        else:
                            mt.restore()

                    # 清空集合資料
                    if info['action']['restore'].get('clear_doc'):
                        backup_logger.info(f'清空集合資料: {collection}')
                        if len(collections) != 0:
                            for collection in collections:
                                mt.delete_all_document()
    backup_logger.info('備份還原完成')
