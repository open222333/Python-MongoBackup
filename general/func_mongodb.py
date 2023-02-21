import os
from . import mongo, DATE_NOW, LOG_LEVEL
from .func_logger import Log


logger = Log(__name__)
logger.set_date_handler()
logger.set_msg_handler()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)


def mongodump(host, db, col, target_dir=f"{os.environ['HOME']}"):
    '''備份 mongo集合 匯出'''
    target_path = f'{target_dir}mongo_backup_{col}/{DATE_NOW}'
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    command = f'mongodump --quiet -h {host} -d {db} -c {col} -o {target_path}'
    logger.debug(f'匯出指令\n{command}')
    os.system(command)
    return DATE_NOW


def mongorestore(host, db, col, target_path, col_name=None):
    '''備份 mongo集合 匯入
    col_name: 備份後集合名稱'''
    if not os.path.exists(target_path):
        logger.debug(f'{target_path} no exists')
        return False
    if col_name == None:
        col_name = col
    command = f'mongorestore -h {host} -d {db} -c {col_name} {target_path}/{db}/{col}.bson'
    logger.debug(f'匯入指令\n{command}')
    os.system(command)
    return True


def drop_collection(db, collections: list):
    '''移除多個集合'''
    try:
        for collection in collections:
            mongo[db][collection].drop()
    except Exception as err:
        logger.error(err, exc_info=True)


def delete_all_document(db, collections: list):
    '''清空指定collections內所有資料'''
    try:
        for collection in collections:
            mongo[db][collection].delete_many({})
    except Exception as err:
        logger.error(err, exc_info=True)
