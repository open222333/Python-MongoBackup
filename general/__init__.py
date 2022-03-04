from configparser import ConfigParser
from pymongo import MongoClient
from datetime import datetime
import json
import os


conf = ConfigParser(os.environ)
conf.read('config.ini', encoding='utf-8')

# 預設備份檔位置
default_dir = f"{os.environ['HOME']}/mongo_backup/"

# 匯出匯入 功能開關
MONGO_DUMP = conf.getint('MONGO_BACKUP', 'MONGO_DUMP', fallback=0)
MONGO_RESTORE = conf.getint('MONGO_BACKUP', 'MONGO_RESTORE', fallback=0)

# 匯出匯入設定
TARGET_PATH = conf.get('MONGO_BACKUP', 'TARGET_PATH', fallback=default_dir)

MONGO_HOST = conf.get('MONGO_BACKUP', 'MONGO_HOST', fallback='127.0.0.1:27017')
MONGO_TARGET_HOST = conf.get(
    'MONGO_BACKUP', 'MONGO_TARGET_HOST', fallback='127.0.0.1:27017')

MONGO_DB = conf.get('MONGO_BACKUP', 'MONGO_DB', fallback=None)
MONGO_COLLECTIONS = json.loads(
    conf.get('MONGO_BACKUP', 'MONGO_COLLECTIONS', fallback=[]))

# 匯入細節設定
COLLECTION_USE_DATA = conf.getint(
    'MONGO_BACKUP', 'COLLECTION_USE_DATA', fallback=1)
DROP_COLLECTIONS = conf.getint(
    'MONGO_BACKUP', 'DROP_COLLECTIONS', fallback=0)

# 日期相關
DATE_NOW = datetime.now().__format__('%Y%m%d')
DATE = conf.get(
    'MONGO_BACKUP', 'DATE', fallback=datetime.now().__format__('%Y%m%d'))

# 依照集合刪除資料 功能開關
DELETE_COLLECTIONS_DOCUMENTS = conf.getint(
    'MONGO_BACKUP', 'DELETE_COLLECTIONS_DOCUMENTS', fallback=0)
DELETE_DB = conf.get('MONGO_BACKUP', 'DELETE_DB', fallback=MONGO_DB)
DELETE_COLLECTIONS = json.loads(
    conf.get('MONGO_BACKUP', 'DELETE_COLLECTIONS', fallback=json.dumps(MONGO_COLLECTIONS)))

# mongo連線
mongo = MongoClient(MONGO_TARGET_HOST)
