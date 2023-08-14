from pymongo import MongoClient
from argparse import ArgumentParser
from src.mongo import MongoRandomSample
from src.progress_bar import ProgressBar
from src import MONGO_INFO
from time import sleep
from threading import Thread

'''
建立測試用資料庫 隨機取得資料
'''

parse = ArgumentParser(description='建立測試用資料庫 隨機取得資料')
parse.add_argument('-H', '--host', type=str, help='主機')
parse.add_argument('-d', '--database', type=str, help='目標資料庫')
parse.add_argument('-c', '--collection', type=str, help='目標集合')
parse.add_argument('--new_collection', type=str, help='隨機建立的集合名稱')
parse.add_argument('-r', '--random', type=int, help='匯入指定數量到集合', default=200)
parse.add_argument('--json', action='store_true', help='根據 mongo.json 執行, 其餘參數將被忽略')
parse.add_argument('--remove_id', action='store_true', help='移除原有_id, 隨機資料建立新_id')
args = parse.parse_args()


def run(host, database, collection, new_collection=None, amount=args.random, remove_id=args.remove_id):
    mrs = MongoRandomSample(
        host=host,
        database=database,
        collection=collection,
        remove_id=remove_id
    )
    client = MongoClient(host)
    mrs.set_sample_size(amount)
    datas = mrs.get_random_datas()

    if new_collection == None:
        new_collection = f'random_{collection}'

    p = ProgressBar(title=f'建立 {database}.{new_collection} ')

    for data in datas:
        p(total=len(datas), in_loop=True)
        client[database][new_collection].insert_one(data)
        sleep(1)


if __name__ == "__main__":
    if args.json:
        for info in MONGO_INFO:
            if info['execute']:
                for database, items in info['action']['random'].items():
                    for collection, item in items.items():
                        threads = []
                        kwargs = {
                            "host": info['host'],
                            "database": database,
                            "collection": collection,
                            "new_collection": item['name']
                        }
                        if item['amount']:
                            kwargs['amount'] = item['amount']
                        thread = Thread(
                            target=run,
                            kwargs=kwargs
                        )
                        threads.append(thread)
                        thread.start()

                    # 等待所有執行緒結束
                    for thread in threads:
                        thread.join()
    else:
        run(
            host=args.host,
            database=args.database,
            collection=args.collection,
            new_collection=args.new_collection
        )
