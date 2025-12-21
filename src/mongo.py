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

    def set_auth(self, username: str, password: str, auth_database: str = 'admin'):
        """設置驗證資料

        Args:
            username (str): 用戶名
            password (str): 密碼
            auth_database (str): 驗證資料庫 預設值
        """
        self.username = username
        self.password = password
        self.auth_database = auth_database

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
        """匯出 Mongo 資料"""
        self.set_date(date=datetime.now().strftime('%Y%m%d'))
        self.generate_backup_dir_path()

        # collection="*" 代表匯出整個資料庫
        if self.collection == "*" or self.collection is None:
            col_option = ""
            mongo_logger.info(f'匯出整個資料庫: {self.database} 至 {self.backup_dir_path}')
        else:
            col_option = f'-c {self.collection}'
            mongo_logger.info(f'匯出 {self.database}.{self.collection} 至 {self.backup_dir_path}')

        # === 組合 mongodump 指令 ===
        command = [
            "mongodump",
            f"-h {self.host}",
            f"-d {self.database}",
            "--quiet"
        ]

        if self.username and self.password:
            command.append(f"-u {self.username}")
            command.append(f"-p {self.password}")
            command.append(f"--authenticationDatabase {self.auth_database}")

        if col_option:
            command.append(col_option)

        command.append(f"-o {self.backup_dir_path}")

        # 組合成字串執行
        command = self.list_convert_str(command)
        mongo_logger.debug(f"執行指令: {command}")

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                mongo_logger.info(f"匯出成功：{self.database}")
            else:
                # 顯示 stderr 或 stdout 任何一邊的錯誤
                err_msg = result.stderr.strip() or result.stdout.strip() or "(無錯誤訊息)"
                mongo_logger.error(f"匯出失敗:\n{err_msg}")

                # 額外 debug：確認隧道仍在
                if hasattr(self, "tunnel"):
                    mongo_logger.debug(f"SSH 隧道狀態: {'開啟' if self.tunnel.is_active else '關閉'}")

                return False

        except Exception as err:
            mongo_logger.error("執行 mongodump 發生例外", exc_info=True)
            return False

        return True

    def restore(self, name: str = None) -> bool:
        """匯入 Mongo 資料"""

        # 設定日期
        if not self.date:
            self.set_date(self.get_lastst_date(self.dir_path))
        else:
            self.generate_backup_dir_path()

        bson_path = f"{self.backup_dir_path}/{self.database}"

        command = [
            "mongorestore",
            f"-h {self.host}",
        ]

        # auth
        if self.username and self.password:
            command.extend([
                f"-u {self.username}",
                f"-p {self.password}",
                f"--authenticationDatabase {self.auth_database}",
            ])

        # 匯入整個資料庫
        if self.collection == "*" or self.collection is None:
            mongo_logger.info(
                f"匯入整個資料庫: {self.database} 從 {bson_path}"
            )
            command.append(bson_path)

        # 匯入單一 collection（新寫法）
        else:
            ns = f"{self.database}.{self.collection}"
            mongo_logger.info(
                f"匯入 {ns} 從 {bson_path}"
            )
            command.append(f"--nsInclude={ns}")
            command.append(bson_path)

        command = self.list_convert_str(command)
        mongo_logger.debug(f"執行指令: {command}")

        try:
            if not os.path.exists(bson_path):
                raise FileNotFoundError(f"{bson_path} 不存在")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                err_msg = result.stderr.strip() or result.stdout.strip() or "(無錯誤訊息)"
                mongo_logger.error(f"匯入失敗:\n{err_msg}")

                if hasattr(self, "tunnel"):
                    mongo_logger.debug(
                        f"SSH 隧道狀態: {'開啟' if self.tunnel.is_active else '關閉'}"
                    )
                return False

            mongo_logger.info(f"匯入成功：{self.database}")
            return True

        except Exception:
            mongo_logger.error("執行 mongorestore 發生例外", exc_info=True)
            return False

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

    def get_size(self) -> dict:
        """
        取得資料庫或集合大小

        Returns:
            dict: 資料庫大小資訊，格式如下：
                {
                    "database": "db_name",
                    "total_data_size": 1234567,   # bytes
                    "total_storage_size": 2345678, # bytes
                    "collections": {
                        "coll1": {"data_size": 123, "storage_size": 234},
                        "coll2": {"data_size": 456, "storage_size": 567}
                    }
                }
        """
        size_info = {
            "database": self.database,
            "total_data_size": 0,
            "total_storage_size": 0,
            "collections": {}
        }

        try:
            # 若 collection == "*" 或 None，則計算整個資料庫
            if self.collection == "*" or self.collection is None:
                for coll_name in self.mongo[self.database].list_collection_names():
                    stats = self.mongo[self.database].command("collstats", coll_name)
                    data_size = stats.get("size", 0)
                    storage_size = stats.get("storageSize", 0)
                    size_info["collections"][coll_name] = {
                        "data_size": data_size,
                        "storage_size": storage_size
                    }
                    size_info["total_data_size"] += data_size
                    size_info["total_storage_size"] += storage_size
                mongo_logger.info(
                    f'資料庫 {self.database} 總大小: {size_info["total_data_size"]/1024/1024:.2f} MB, '
                    f'儲存大小: {size_info["total_storage_size"]/1024/1024:.2f} MB'
                )
            else:
                stats = self.mongo[self.database].command("collstats", self.collection)
                data_size = stats.get("size", 0)
                storage_size = stats.get("storageSize", 0)
                size_info["collections"][self.collection] = {
                    "data_size": data_size,
                    "storage_size": storage_size
                }
                size_info["total_data_size"] = data_size
                size_info["total_storage_size"] = storage_size
                mongo_logger.info(
                    f'集合 {self.database}.{self.collection} 大小: {data_size/1024/1024:.2f} MB, '
                    f'儲存大小: {storage_size/1024/1024:.2f} MB'
                )

        except Exception as e:
            mongo_logger.error(f'取得大小失敗: {e}', exc_info=True)
            return {}

        return size_info


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
        mongo_logger.info(f'建立 SSH 隧道: {ssh_user}@{ssh_host}:{ssh_port} -> {mongo_host}:{mongo_port}')
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
            mongo_logger.info("關閉 SSH 隧道")
            self.tunnel.stop()
