from general.func_mongodb import mongodump, mongorestore
from general.func_mongodb import drop_collection, delete_all_document
from general.func_tool import get_lastst_date
from general import MONGO_COLLECTIONS,  MONGO_DB
from general import MONGO_HOST, TARGET_PATH, MONGO_TARGET_HOST
from general import MONGO_DUMP, MONGO_RESTORE
from general import DATE, COLLECTION_USE_DATA, DROP_COLLECTIONS
from general import DELETE_COLLECTIONS_DOCUMENTS, DELETE_DB, DELETE_COLLECTIONS
from general import LOG_LEVEL
from general.func_logger import Log
import os


logger = Log(__name__)
logger.set_date_handler()
logger.set_msg_handler()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)


# 執行匯出
if MONGO_DUMP:
    if len(MONGO_COLLECTIONS) != 0:
        for col in MONGO_COLLECTIONS:
            logger.info(f'執行匯出 host:{MONGO_HOST} target_path:{TARGET_PATH} db:{MONGO_DB} col: {col}')
            mongodump(
                host=MONGO_HOST,
                db=MONGO_DB,
                col=col,
                target_dir=TARGET_PATH
            )

# 執行匯入
if MONGO_RESTORE:

    # 刪除目前的集合
    if DROP_COLLECTIONS:
        if len(MONGO_COLLECTIONS) != 0:
            logger.info(f'執行匯入 刪除目前的集合 {MONGO_DB} {MONGO_COLLECTIONS}')
            drop_collection(MONGO_DB, MONGO_COLLECTIONS)

    for col in MONGO_COLLECTIONS:
        target = f'{TARGET_PATH}mongo_backup_{col}/{DATE}'

        # 若無設定日期 會以最新日期進行備份
        if not os.path.exists(target):
            lastst_date = get_lastst_date(f'{TARGET_PATH}mongo_backup_{col}')
            target = f'{TARGET_PATH}mongo_backup_{col}/{lastst_date}'

        # 集合名稱不帶日期
        col_name = None
        if COLLECTION_USE_DATA:
            col_name = f'{col}_{DATE}'

        logger.info(f'執行匯入 host:{MONGO_TARGET_HOST} target_path:{target} db:{MONGO_DB} col: {col_name}')
        mongorestore(
            host=MONGO_TARGET_HOST,
            db=MONGO_DB,
            col=col,
            target_path=target,
            col_name=col_name
        )

# 清空集合資料
if DELETE_COLLECTIONS_DOCUMENTS:
    if len(DELETE_COLLECTIONS) != 0:
        for col in DELETE_COLLECTIONS:
            logger.info(f'清空集合資料 {col}')
            delete_all_document(DELETE_DB, DELETE_COLLECTIONS)
