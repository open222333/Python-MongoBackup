from .logger import Log
from . import LOG_LEVEL
import os


logger = Log()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)

logger.set_date_handler()
logger.set_msg_handler()


def get_all_files(dir_path, extensions=None):
    '''取得所有檔案
    dir_path: 檔案資料夾
    extensions: 指定副檔名,若無指定則全部列出
    '''
    target_file_path = []
    path = os.path.abspath(dir_path)

    for file in os.listdir(path):
        _, file_extension = os.path.splitext(file)
        if extensions:
            allow_extension = [f'.{e}' for e in extensions]
            if file_extension in allow_extension:
                target_file_path.append(f'{dir_path}/{file}')
        else:
            target_file_path.append(f'{dir_path}/{file}')

        # 遞迴
        if os.path.isdir(f'{dir_path}/{file}'):
            files = get_all_files(f'{dir_path}/{file}', extensions)
            for file in files:
                target_file_path.append(file)
    target_file_path.sort()
    return target_file_path


def parse_db_collections(path):
    """解析 資料夾內容取得備份下來的 db collections

    Args:
        path (_type_): _description_

    Returns:
        { 'dbname' : [collection1, ... ]}
    """
    items = {}
    all_files = get_all_files(path, ['bson'])
    for file in all_files:
        dirname = os.path.basename(os.path.dirname(file))
        file, _ = os.path.splitext(os.path.basename(file))

        if dirname not in items.keys():
            items[dirname] = [file]
        else:
            items[dirname].append(file)
    return items
