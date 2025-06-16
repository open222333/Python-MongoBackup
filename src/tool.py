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

def print_config(config):
    """列印配置說明
    Args:
        config (list): 配置列表
    """
    for i, task in enumerate(config, 1):
        print(f"\n🔧 任務 {i}")
        print(f"👉 是否執行: {'是' if task['execute'] else '否'}")

        # dump 說明
        dump = task['action']['dump']
        print("\n📤 匯出 (Dump):")
        if dump.get("items"):
            for item in dump["items"]:
                db = item.get("database")
                cols = item.get("collections", [])
                if db and cols:
                    print(f"  - 資料庫: {db}")
                    print(f"    匯出集合: {', '.join(cols)}")
                else:
                    print("  ❗ 資料庫名稱或集合為空，請檢查 dump 設定")
        else:
            print("  ❗ 未設定任何要匯出的資料庫或集合")

        # restore 說明
        restore = task["action"]["restore"]
        print("\n📥 還原 (Restore):")
        print(f"  - 還原日期: {restore.get('date', '未設定')}")
        print(f"  - 是否刪除原集合: {'是' if restore.get('drop_collection') else '否'}")
        print(f"  - 是否清空文件再導入: {'是' if restore.get('clear_doc') else '否'}")
        print(f"  - 是否附加日期欄位: {'是' if restore.get('attach_date') else '否'}")
        if restore.get("items"):
            for item in restore["items"]:
                db = item.get("database")
                cols = item.get("collections", [])
                if db and cols:
                    print(f"  - 資料庫: {db}")
                    print(f"    還原集合: {', '.join(cols)}")
                else:
                    print("  ❗ 資料庫名稱或集合為空，請檢查 restore 設定")
        else:
            print("  ❗ 未設定任何要還原的資料庫或集合")

        # random 說明
        print("\n🎲 隨機抽樣/重新命名 (Random):")
        random = task["action"].get("random", {})
        if not random:
            print("  ❗ 未設定 random 內容")
        else:
            for db_name, collections in random.items():
                if not collections:
                    print(f"  - 資料庫: {db_name} ❗ 無任何集合設定")
                    continue
                print(f"  - 資料庫: {db_name}")
                for old_name, info in collections.items():
                    new_name = info.get("name")
                    amount = info.get("amount")
                    if not new_name:
                        print(f"    集合「{old_name}」 ❗ 未設定新名稱")
                    else:
                        print(f"    集合「{old_name}」 → 新名稱: 「{new_name}」")
                    if amount:
                        print(f"      抽樣數量: {amount}")
                    else:
                        print("      （未設定抽樣數量，預設導入全部）")
