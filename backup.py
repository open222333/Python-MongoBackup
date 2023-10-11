from argparse import ArgumentParser
from src import MONGO_INFO, OUTPUT_DIR
from src.mongo import MongoTool
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
        if info['execute']:

            # 執行匯出
            if info['action'].get('dump'):
                if info['action']['dump']['execute']:

                    if info['action']['dump']['host']:
                        host = info['action']['dump']['host']
                    else:
                        host = '127.0.0.1'

                    if info['action']['dump']['port']:
                        port = info['action']['dump']['port']
                    else:
                        port = '27017'

                    username = info['action']['dump']['username']
                    password = info['action']['dump']['password']

                    if info['action']['dump']['hostname']:
                        hostname = info['action']['dump']['hostname']
                    else:
                        hostname = socket.gethostname()

                    for item in info['action']['dump']['items']:
                        database = item['database']
                        collections = item['collections']
                        if len(collections) == 0:
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
                            mt.dump()

            # 執行匯入
            if info['action'].get('restore'):
                if info['action']['restore']['execute']:

                    if info['action']['restore']['host']:
                        host = info['action']['restore']['host']
                    else:
                        host = '127.0.0.1'

                    if info['action']['restore']['port']:
                        port = info['action']['restore']['port']
                    else:
                        port = '27017'

                    username = info['action']['restore']['username']
                    password = info['action']['restore']['password']

                    for item in info['action']['restore']['items']:
                        database = item['database']
                        collections = item['collections']

                        if info['action']['restore']['hostname']:
                            hostname = info['action']['restore']['hostname']
                        else:
                            hostname = socket.gethostname()

                        if len(collections) == 0:
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
                            if info['action']['restore']['drop_collection']:
                                mt.drop_collection()

                            if info['action']['restore']['date']:
                                mt.set_date(date=info['action']['restore']['date'])
                            # 集合名稱不帶日期
                            if info['action']['restore']['attach_date']:
                                mt.restore(name=f'{collection}_{mt.date}')
                            else:
                                mt.restore()

                        # 清空集合資料
                        if info['action']['restore']['clear_doc']:
                            if len(collections) != 0:
                                for collection in collections:
                                    mt.delete_all_document()
