from . import LOG_LEVEL, LOG_FILE_DISABLE
from .logger import Log
from datetime import datetime
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from typing import Union
import os
import re
import subprocess


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


class MongoToolSSH(MongoTool):
    def __init__(self, host, database, collection, dir_path, date=None,
                 ssh_host=None, ssh_port=22, ssh_user=None, ssh_password=None,
                 ssh_key_path=None, use_key=False):

        mongo_host, mongo_port = host.split(':')
        mongo_port = int(mongo_port)

        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_key_path = ssh_key_path
        self.use_key = use_key
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port

        # === 建立 SSH 隧道 ===
        tunnel_args = dict(
            ssh_address_or_host=(ssh_host, ssh_port),
            ssh_username=ssh_user,
            remote_bind_address=(mongo_host, mongo_port),
            local_bind_address=('127.0.0.1',)
        )

        # 若使用 key 登入
        if use_key and ssh_key_path:
            tunnel_args['ssh_pkey'] = ssh_key_path
        else:
            tunnel_args['ssh_password'] = ssh_password

        self.tunnel = SSHTunnelForwarder(**tunnel_args)
        self.tunnel.start()

        local_port = self.tunnel.local_bind_port

        # === 重新初始化 MongoTool (連接 SSH 本地端口) ===
        super().__init__(
            host=f"127.0.0.1:{local_port}",
            database=database,
            collection=collection,
            dir_path=dir_path,
            date=date
        )

    def close_ssh(self):
        """關閉 SSH 隧道"""
        if hasattr(self, "tunnel") and self.tunnel.is_active:
            self.tunnel.stop()
