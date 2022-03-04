from general.mongodb_function import mongodump, mongorestore
from general.mongodb_function import drop_collection, delete_all_document
from general.tool_function import get_lastst_date
from general import MONGO_COLLECTIONS,  MONGO_DB
from general import MONGO_HOST, TARGET_PATH, MONGO_TARGET_HOST
from general import MONGO_DUMP, MONGO_RESTORE
from general import DATE, COLLECTION_USE_DATA, DROP_COLLECTIONS
from general import DELETE_COLLECTIONS_DOCUMENTS, DELETE_DB,DELETE_COLLECTIONS
import os

# 執行
if MONGO_DUMP:
    if len(MONGO_COLLECTIONS) != 0:
        for col in MONGO_COLLECTIONS:
            mongodump(
                host=MONGO_HOST,
                db=MONGO_DB,
                col=col,
                target_dir=TARGET_PATH
            )

if MONGO_RESTORE:
    if len(MONGO_COLLECTIONS) != 0:
    # 刪除目前的集合
        if DROP_COLLECTIONS:
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
                
            mongorestore(
                host=MONGO_TARGET_HOST,
                db=MONGO_DB,
                col=col,
                target_path=target,
                col_name=col_name
            )

if DELETE_COLLECTIONS_DOCUMENTS:
    if len(DELETE_COLLECTIONS) != 0:
        for col in DELETE_COLLECTIONS:
            delete_all_document(DELETE_DB, DELETE_COLLECTIONS)
    