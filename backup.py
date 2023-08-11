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
            host = info['host']
            if info['hostname']:
                hostname = info['hostname']
            else:
                hostname = socket.gethostname()
            for item in info['items']:
                database = item['database']
                collections = item['collections']
                if len(collections) == 0:
                    continue
                # 執行匯出
                if info['action']['dump']['execute']:
                    for collection in collections:
                        mt = MongoTool(
                            host=info['host'],
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )
                        mt.dump()
                # 執行匯入
                if info['action']['restore']['execute']:
                    for collection in collections:
                        mt = MongoTool(
                            host=info['host'],
                            database=database,
                            collection=collection,
                            dir_path=os.path.join(OUTPUT_DIR, hostname)
                        )
                        # 刪除目前的集合
                        if info['action']['restore']['drop_collection']:
                            mt.drop_collection()

                        for collection in collections:
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
