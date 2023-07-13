from pymongo import MongoClient
from argparse import ArgumentParser
from src.mongo import MongoRandomSample

parse = ArgumentParser()
parse.add_argument('-h', '--host', type=str, help='主機', required=True)
parse.add_argument('-d', '--database', type=str, help='資料庫', required=True)
parse.add_argument('-c', '--collection', type=str, help='集合', required=True)
parse.add_argument('-r', '--random', type=int, help='匯入指定數量到集合', default=200)
args = parse.parse_args()

if __name__ == "__main__":
    mrs = MongoRandomSample(
        host=args.host,
        database=args.database,
        collection=args.collection
    )
    client = MongoClient(args.host)
    mrs.set_query(args.random)
    datas = mrs.get_random_datas()
    for data in datas:
        client[args.database][args.collection].insert_one(data)
