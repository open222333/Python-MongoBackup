from .logger import Log
from . import LOG_LEVEL, LOG_FILE_DISABLE
from pymongo import MongoClient
import traceback
import random
import json
import re

mongo_logger = Log('MONGO_RANDOM')
if LOG_LEVEL:
    mongo_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    mongo_logger.set_date_handler()
mongo_logger.set_msg_handler()


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

    def get_all_databases(self):
        try:
            db_names = self.client.list_database_names()
        except Exception:
            db_names = []

        # 如果 self.databases 有指定資料庫
        if self.databases:
            # 把 self.databases 裡的資料庫加入，若還沒在 db_names 中
            for db_name in self.databases:
                if db_name not in db_names:
                    db_names.append(db_name)
            # 過濾只保留 self.databases 中的資料庫
            db_names = [db_name for db_name in db_names if db_name in self.databases]

        return db_names

    def get_all_collections(self):
        items = {}
        database_names = self.get_all_databases()
        for db_name in database_names:
            db = self.client[db_name]
            collection_names = db.list_collection_names()
            for collection_name in collection_names:
                if db_name not in items.keys():
                    items[db_name] = [collection_name]
                else:
                    items[db_name].append(collection_name)
                # print(f"Database: {db_name}, Collection: {collection_name}")
        return items

    def get_all_collections_by_a_database(self, database: str):
        """
        取得單一資料庫的所有集合名稱。
        即使帳號沒有權限列出資料庫，也能嘗試取得指定資料庫的集合。

        Args:
            database (str): 要查詢的資料庫名稱

        Returns:
            list: 資料庫的集合名稱列表，若無法取得則回傳空列表
        """
        try:
            collections = self.client[database].list_collection_names()
        except Exception as err:
            mongo_logger.warning(f"無法取得 {database} 的集合: {err}")
            collections = []

        return collections


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
