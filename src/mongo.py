import os
import random
import subprocess
from typing import Union
from datetime import datetime
from pymongo import MongoClient
from .logger import Log
from . import LOG_LEVEL, LOG_FILE_DISABLE


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

        if date:
            self.date = date
        else:
            self.date = datetime.now().__format__('%Y%m%d')

        self.backup_dir_path = f'{self.dir_path}/{self.date}'
        if not os.path.exists(self.backup_dir_path):
            os.makedirs(self.backup_dir_path)

    def set_dir_path(self, dir_path: str):
        """設置 備份檔放置路徑

        Args:
            dir_path (str): 資料夾路徑
        """
        self.dir_path = dir_path
        self.backup_dir_path = f'{self.dir_path}/{self.date}'

    def set_date(self, date: str):
        """設置 日期

        Args:
            date (str): 20230101
        """
        self.date = date

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
        mongo_logger.info(f'匯出  {self.database} {self.collection} 至 {self.backup_dir_path}')
        command = ['mongodump', '--quiet', f'-h {self.host}', f'-d {self.database}']
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
                mongo_logger.debug(f'結果:\n{result.stderr}')
            else:
                mongo_logger.error(f'錯誤:\n{result.stderr}')
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
            documents = list(self.client[self.database][self.collection].find(self.query))
        else:
            documents = list(self.client[self.database][self.collection].find())

        if self.remove_id:
            mongo_logger.info('移除 隨機資料 _id欄位')
            for doc in documents:
                doc.pop('_id', None)

        random_documents = random.sample(documents, min(len(documents), self.sample_size))
        return random_documents
