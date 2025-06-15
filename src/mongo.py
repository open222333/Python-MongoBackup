from . import LOG_LEVEL, LOG_FILE_DISABLE
from .logger import Log
from datetime import datetime
from pymongo import MongoClient
from typing import Union
import json
import os
import random
import re
import subprocess
import traceback


mongo_logger = Log('MONGO')
if LOG_LEVEL:
    mongo_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    mongo_logger.set_date_handler()
mongo_logger.set_msg_handler()


class MongoTool():

    def __init__(self, host: str, database: str, collection: str, dir_path: str, date: str = None) -> None:
        # mongo連線 匯入
        self.mongo = MongoClient(host)
        self.host = host
        self.database = database
        self.collection = collection
        self.dir_path = dir_path

        self.username = None
        self.password = None

        self.date = date

    def generate_backup_dir_path(self):
        self.backup_dir_path = f'{self.dir_path}/{self.date}'
        if not os.path.exists(self.backup_dir_path):
            os.makedirs(self.backup_dir_path)

    def set_dir_path(self, dir_path: str):
        """設置 備份檔放置路徑

        Args:
            dir_path (str): 資料夾路徑
        """
        self.dir_path = dir_path
        self.generate_backup_dir_path()

    def set_date(self, date: str):
        """設置 日期

        Args:
            date (str): 20230101
        """
        self.date = date
        self.generate_backup_dir_path()

    def set_auth(self, username: str, password: str, database: str = 'admin'):
        """設置驗證資料

        Args:
            username (str): 用戶名
            password (str): 密碼
            database (str): 驗證資料庫 預設值
        """
        self.username = username
        self.password = password
        self.auth_database = database

    def list_convert_str(self, strs: list):
        """將串列轉成字串

        Args:
            strs (list): _description_

        Returns:
            _type_: _description_
        """
        string = ''
        for i in range(len(strs)):
            if i != len(strs) - 1:
                string += f'{strs[i]} '
            else:
                string += strs[i]
        return string

    def get_lastst_date(self, path: str) -> Union[dict, None]:
        """取得最新日期的資料夾名稱

        檔名格式 = '%Y%m%d'

        Args:
            path (str): 目標資料夾

        Returns:
            Union[dict, None]: _description_
        """
        date_dirs = os.listdir(path)
        format_date = '%Y%m%d'
        stock = {}
        for date in date_dirs:
            try:
                stock[datetime.strptime(date, format_date)] = date
            except Exception as err:
                mongo_logger.error(err, exc_info=True)
                return None
        return stock[max(stock.keys())]

    def dump(self) -> bool:
        """匯出

        Returns:
            bool: _description_
        """
        self.set_date(date=datetime.now().__format__('%Y%m%d'))

        mongo_logger.info(f'匯出  {self.database} {self.collection} 至 {self.backup_dir_path}')
        command = ['mongodump', '--quiet',
                   f'-h {self.host}', f'-d {self.database}']
        if self.username != None and self.password != None:
            command.append(f'-u {self.username}')
            command.append(f'-p {self.password}')
            command.append(f'--authenticationDatabase {self.auth_database}')
        command.append(f'-c {self.collection}')
        command.append(f'-o {self.backup_dir_path}')

        command = self.list_convert_str(command)
        mongo_logger.debug(command)

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # mongo_logger.debug(f'結果:\n{result.stderr}')
                pass
            else:
                mongo_logger.error(f'匯出失敗:\n{result.stderr}')
                # mongo_logger.error(f'錯誤:\n{result.stderr}')
        except Exception as err:
            mongo_logger.error(err, exc_info=True)
            return False
        return True

    def restore(self, name: str = None) -> bool:
        """匯入 mongo集合

        Args:
            name (str, optional): 備份後集合名稱. Defaults to None.

        Returns:
            _type_: _description_
        """
        if self.date == None:
            dates = []
            files = os.listdir(self.dir_path)

            date_pattern = r'(\d{4})(\d{2})(\d{2})'

            for file in files:
                if os.path.isdir(f'{self.dir_path}/{file}'):
                    match = re.match(date_pattern, file)
                    if match:
                        dates.append(file)

            if len(dates) == 0:
                raise RuntimeError(f'{self.dir_path} 內沒有任何備份')

            last_date = max([datetime.strptime(date, "%Y%m%d") for date in dates]).strftime("%Y%m%d")
            self.set_date(date=last_date)
        else:
            self.set_date(date=self.date)

        bson_file = f'{self.backup_dir_path}/{self.database}/{self.collection}.bson'

        command = ['mongorestore', f'-h {self.host}', f'-d {self.database}']
        if name:
            mongo_logger.info(f'匯入 {bson_file} 至 {self.database} {name}')
            command.append(f'-c {name}')
            if self.username != None and self.password != None:
                command.append(f'-u {self.username}')
                command.append(f'-p {self.password}')
                command.append(f'--authenticationDatabase {self.auth_database}')
            command.append(bson_file)
        else:
            mongo_logger.info(f'匯入 {bson_file} 至 {self.database} {self.collection}')
            command.append(f'-c {self.collection}')
            if self.username != None and self.password != None:
                command.append(f'-u {self.username}')
                command.append(f'-p {self.password}')
                command.append(f'--authenticationDatabase {self.auth_database}')
            command.append(bson_file)

        command = self.list_convert_str(command)

        try:
            if os.path.exists(bson_file):
                mongo_logger.debug(f'指令\n{command}')
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    mongo_logger.debug(f'結果:\n{result.stderr}')
                else:
                    mongo_logger.error(f'錯誤:\n{result.stderr}')
            else:
                raise FileNotFoundError(f'{bson_file} 不存在')
        except Exception as err:
            mongo_logger.error(err, exc_info=True)
            return False
        return True

    def drop_collection(self) -> bool:
        '''移除collection'''
        try:
            mongo_logger.info(f'刪除 {self.database} {self.collection}')
            self.mongo[self.database][self.collection].drop()
        except Exception as err:
            mongo_logger.error(err, exc_info=True)
            return False
        return True

    def delete_all_document(self) -> bool:
        '''清空collection內所有資料'''
        try:
            mongo_logger.info(f'刪除 {self.database} {self.collection} 內所有資料')
            self.mongo[self.database][self.collection].delete_many({})
        except Exception as err:
            mongo_logger.error(err, exc_info=True)
            return False
        return True


class MongoRandomSample():

    def __init__(self, host: str, database: str, collection: str, remove_id: bool = True) -> None:
        """抽樣指定資料庫以及集合的資料,數量預設為200

        Args:
            host (str): 主機
            db (str): 要抽取樣本的資料庫名稱
            collection (str): 要抽取樣本的集合名稱
            remove_id (bool): 刪除_id, 隨機資料以新的_id建立. Default to True.
        """
        self.sample_size = 200
        self.client = MongoClient(host)
        self.database = database
        self.collection = collection
        self.query = None
        self.remove_id = remove_id

    def set_sample_size(self, size: int):
        """設置樣本數量

        Args:
            size (int): 指定數量
        """
        self.sample_size = size

    def set_query(self, **kwargs):
        """設置搜尋條件
        """
        self.query = kwargs

    def get_random_datas(self):
        """取得樣本

        Returns:
            list: mongo文件
        """
        if self.query:
            documents = list(
                self.client[self.database][self.collection].find(self.query))
        else:
            documents = list(
                self.client[self.database][self.collection].find())

        if self.remove_id:
            mongo_logger.info('移除 隨機資料 _id欄位')
            for doc in documents:
                doc.pop('_id', None)

        random_documents = random.sample(
            documents, min(len(documents), self.sample_size))
        return random_documents


class MongoMappingCollections():

    def __init__(self, host: str) -> None:
        self.client = MongoClient(host)
        self.databases = None

    def set_databases(self, *databases: str):
        self.databases = databases

    def get_all_collections(self):
        items = {}
        database_names = self.client.list_database_names()
        for db_name in database_names:
            if self.databases:
                if db_name not in self.databases:
                    continue
            db = self.client[db_name]
            collection_names = db.list_collection_names()
            for collection_name in collection_names:
                if db_name not in items.keys():
                    items[db_name] = [collection_name]
                else:
                    items[db_name].append(collection_name)
                # print(f"Database: {db_name}, Collection: {collection_name}")
        return items


def get_filter_trans_jqGrid_to_pymongo(filters, *is_int: str, **multi_column: list):
    """轉換篩選條件 js jqGrid 為 python pymongo

    Args:
        filters (_type_): _description_
        is_int: 輸入欄位 欲指定型態int,
        multi_column: 多重標題 *為任何，範例：title=[viedos.ko.title, videos.zh-Hant.title]

    Returns:
        _type_:  回傳 msg
            {
                'status': bool,
                'message': 錯誤訊息(status = False 才會回傳),
                'result': 轉換結果,
                'rules': 搜尋的條件資料，格式為
                    [
                        {
                            'filed': 欄位,
                            'op': 運算子,
                            'data': 資料
                        }, ......
                    ]
            }
    """
    def get_op(filed, data, op):
        op_dict = {
            'eq': {filed: {'$eq': data}},  # 等於
            'ne': {filed: {'$ne': data}},  # 不等於
            'lt': {filed: {'$lt': data}},  # 小於
            'le': {filed: {'$lte': data}},  # 小於等於
            'gt': {filed: {'$gt': data}},  # 大於
            'ge': {filed: {'$gte': data}},  # 大於等於
            'bw': {filed: {'$regex': f'^{data}'}},  # 開頭是
            'bn': {filed: {'$not': {'$regex': f'^{data}'}}},  # 開頭不是
            'in': {filed: {'$elemMatch': {'$eq': data}}},  # 在其中
            'ni': {filed: {'$not': {'$elemMatch': {'$eq': data}}}},  # 不在其中
            'ew': {filed: {'$regex': f'${data}'}},  # 結尾是
            'en': {filed: {'$not': {'$regex': f'${data}'}}},  # 結尾不是
            # 'cn': {filed: {'$in': [data]}},  # 內容包含(需用array)
            # 'nc': {filed: {'$nin': [data]}},  # 內容不包含(需用array)
            'cn': {filed: {'$regex': data}},  # 內容包含
            'nc': {filed: {'$not': {'$regex': data}}},  # 內容不包含
        }
        if op not in op_dict.keys():
            return None
        else:
            op = op_dict[op]
            return op

    filters = json.loads(filters)

    groupOp = filters['groupOp']
    rules = filters['rules']
    msg_rules = []

    mongo_filter = {}
    msg = {}

    # 轉換 運算子
    group_op_dict = {
        'AND': '$and',
        'OR': '$or'
    }

    # 轉換 jqGrid op為 pymongo op
    if groupOp in group_op_dict:
        groupOp = group_op_dict[groupOp]
    else:
        msg['status'] = False
        msg['message'] = f'groupOp: {groupOp} 沒有設定'
        return msg

    # 拆解 搜尋條件
    rule_stock = []
    for rule in rules:
        filed = rule['field']
        op = rule['op']
        data = rule['data']

        # 若有欄位指定型態int
        if filed in is_int and data != "":
            try:
                data = int(data)
            except:
                msg['status'] = False
                msg['message'] = traceback.format_exc()
                return msg

        # 若有多重欄位
        if filed in multi_column.keys():
            if not isinstance(multi_column[filed], list):
                filed_stack = list(multi_column[filed])
            else:
                filed_stack = multi_column[filed]
            multi = True
        else:
            multi = False

        # 轉換 true false
        if data == 'true':
            data = True
        elif data == 'false':
            data = False

        # 轉換
        trans_regex_ops = ['cn', 'nc']  # 使用正則
        if op in trans_regex_ops:
            # 轉換 regex
            data = re.compile(f'.*{data}.*')

        try:
            # 整理最後搜尋條件
            if multi:
                # 若是篩選多重欄位
                rule_temps = []
                for filed_temp in filed_stack:
                    rule_temp = get_op(filed_temp, data, op)
                    if rule_temp != None:
                        rule_temps.append(rule_temp)
                    else:
                        msg['status'] = False
                        msg['message'] = f'op: {op} 沒有設定'
                        return msg
                rule_stock.append({'$or': rule_temps})
            else:
                rule_temp = get_op(filed, data, op)
                if rule_temp != None:
                    rule_stock.append(rule_temp)
                else:
                    msg['status'] = False
                    msg['message'] = f'op: {op} 沒有設定'
                    return msg
            # 使用的規則
            msg_rules.append(
                {
                    'filed': filed,
                    'op': op,
                    'data': data
                }
            )
        except:
            msg['status'] = False
            msg['message'] = traceback.format_exc()
            return msg

    mongo_filter[groupOp] = rule_stock
    msg['status'] = True
    msg['result'] = mongo_filter
    msg['rules'] = msg_rules
    return msg
