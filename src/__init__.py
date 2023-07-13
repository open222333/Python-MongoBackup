from configparser import ConfigParser
import logging
import json
import os


conf = ConfigParser(os.environ)
conf.read('.conf/config.ini', encoding='utf-8')

# 預設備份檔位置
default_dir = f"{os.environ['HOME']}/mongo_backup/"

# logs相關參數
# 關閉log功能 輸入選項 (true, True, 1) 預設 不關閉
LOG_DISABLE = conf.getboolean('LOG', 'LOG_DISABLE', fallback=False)
# logs路徑 預設 logs
LOG_PATH = conf.get('LOG', 'LOG_PATH', fallback='logs')
# 設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
LOG_LEVEL = conf.get('LOG', 'LOG_LEVEL', fallback='WARNING')
# 關閉紀錄log檔案 輸入選項 (true, True, 1)  預設 關閉
LOG_FILE_DISABLE = conf.getboolean('LOG', 'LOG_FILE_DISABLE', fallback=True)

if LOG_DISABLE:
    logging.disable()

JSON_PATH = conf.get('SETTING', 'JSON_PATH', fallback='.conf/mongo.json')
with open(JSON_PATH, 'r') as f:
    MONGO_INFO = json.loads(f.read())

# 設定放置備份檔案資料夾位置 預設 output/
OUTPUT_DIR = conf.get('SETTING', 'OUTPUT_DIR', fallback='output')
