from argparse import ArgumentParser
from src import MONGO_INFO, OUTPUT_DIR
from src.mongo import MongoTool, MongoMappingCollections
from src.tool import parse_db_collections
import socket
import os

'''
備份-還原 範本

根據 conf/mongo.json 執行
'''


parser = ArgumentParser(description='批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行')
args = parser.parse_args()

if __name__ == "__main__":
    for info in MONGO_INFO:
        if info.get('execute'):

            # 執行匯出
            if info['action'].get('dump'):

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
                        mmc = MongoMappingCollections(f'{host}:{port}')
                        mmc.set_databases(database)
                        collections = mmc.get_all_collections()[database]

                    for collection in collections:
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
                            collections = parse_db_collections(item.get('dirpath'))[database]
                        else:
                            continue

                    for collection in collections:
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
                            mt.drop_collection()

                        # 指定日期
                        if info['action']['restore'].get('date'):
                            mt.set_date(date=info['action']['restore']['date'])

                        # 集合名稱不帶日期
                        if info['action']['restore'].get('attach_date'):
                            mt.restore(name=f'{collection}_{mt.date}')
                        else:
                            mt.restore()

                    # 清空集合資料
                    if info['action']['restore'].get('clear_doc'):
                        if len(collections) != 0:
                            for collection in collections:
                                mt.delete_all_document()
