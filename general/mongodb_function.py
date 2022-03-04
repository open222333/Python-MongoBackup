import os
import traceback
from . import mongo, DATE_NOW


def mongodump(host, db, col, target_dir=f"{os.environ['HOME']}"):
    '''備份 mongo集合 匯出'''
    target_path = f'{target_dir}mongo_backup_{col}/{DATE_NOW}'
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    command = f'mongodump --quiet -h {host} -d {db} -c {col} -o {target_path}'
    print(command)
    os.system(command)
    return DATE_NOW


def mongorestore(host, db, col, target_path, col_name=None):
    '''備份 mongo集合 匯入
    col_name: 備份後集合名稱'''
    if not os.path.exists(target_path):
        print(f'{target_path} no exists')
        return False
    if col_name == None:
        col_name = col
    command = f'mongorestore -h {host} -d {db} -c {col_name} {target_path}/{db}/{col}.bson'
    os.system(command)
    return True


def drop_collection(db, collections: list):
    '''移除多個集合'''
    try:
        for collection in collections:
            mongo[db][collection].drop()
    except:
        traceback.print_exc()


def delete_all_document(db, collections: list):
    '''清空指定collections內所有資料'''
    try:
        for collection in collections:
            mongo[db][collection].delete_many({})
    except:
        traceback.print_exc()
