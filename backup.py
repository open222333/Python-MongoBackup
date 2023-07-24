from argparse import ArgumentParser
from datetime import datetime
from src import MONGO_INFO, OUTPUT_DIR
from src.mongo import MongoTool
import os

'''
備份-還原 範本

根據 .conf/mongo.json 執行
'''


parser = ArgumentParser()
group = parser.add_argument_group(title='功能', description='可使用json設置是否使用以下功能')
group.add_argument('-d', '--dump', action='store_true', help='匯出')
group.add_argument('-r', '--restore', action='store_true', help='匯入')
restore_group = parser.add_argument_group(title='匯入附加功能', description='匯入時使用')
restore_group.add_argument('--date', type=str, help='日期')
restore_group.add_argument('--drop_collection', action='store_true', help='刪除目前集合')
restore_group.add_argument('--clear_doc', action='store_true', help='清除collection內文檔')
restore_group.add_argument('--attach_date', action='store_true', help='集合名稱附加日期')
args = parser.parse_args()

if __name__ == "__main__":
    for info in MONGO_INFO:
        if info['execute']:
            host = info['host']
            database = info['database']
            collections = str(info['collections']).split(',')
            if args.date:
                date = args.date
            else:
                date = datetime.now()

            if len(collections) == 0:
                continue
            # 執行匯出
            if args.dump or info['dump']:
                for collection in collections:
                    mt = MongoTool(
                        host=info['host'],
                        database=database,
                        collection=collection,
                        dir_path=OUTPUT_DIR
                    )
                    mt.dump()
            # 執行匯入
            if args.restore or info['restore']:
                for collection in collections:
                    mt = MongoTool(
                        host=info['host'],
                        database=database,
                        collection=collection,
                        dir_path=OUTPUT_DIR
                    )
                    # 刪除目前的集合
                    if args.drop_collection:
                        mt.drop_collection()

                    for collection in collections:
                        target = f'{OUTPUT_DIR}/{collection}/{date}'

                        # 若無設定日期 會以最新日期進行備份
                        if not os.path.exists(OUTPUT_DIR):
                            lastst_date = mt.get_lastst_date(f'{OUTPUT_DIR}/{collection}')
                            target = f'{OUTPUT_DIR}/{collection}/{lastst_date}'

                        # 集合名稱不帶日期
                        if args.attach_date:
                            mt.restore(name=f'{collection}_{date}')
                        else:
                            mt.restore()

                # 清空集合資料
                if args.clear_doc:
                    if len(collections) != 0:
                        for collection in collections:
                            mt.delete_all_document()
