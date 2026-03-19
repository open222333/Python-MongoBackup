from .logger import Log
from . import LOG_LEVEL, OUTPUT_DIR
from datetime import datetime
import socket
import os

logger = Log(log_name='TOOL')
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)

# logger.set_date_handler()
logger.set_msg_handler()


def get_lastst_date(path: str):
    """取得最新日期的資料夾名稱

    檔名格式 = '%Y%m%d'

    Args:
        path (str): 目標資料夾

    Returns:
        Union[dict, None]: _description_
    """
    if not os.path.exists(path):
        # logger.error(f'路徑不存在: {path}')
        return None
    date_dirs = os.listdir(path)
    format_date = '%Y%m%d'
    stock = {}
    for date in date_dirs:
        try:
            stock[datetime.strptime(date, format_date)] = date
        except ValueError:
            logger.debug(f"跳過非日期項目: {date!r}")
            continue
    return stock[max(stock.keys())]


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
    dump_collections = {}

    for i, task in enumerate(config, 1):
        logger.info(f"===================")
        logger.info(f"🔧 任務 {i}")
        logger.info(f"👉 是否執行: {'是' if task['execute'] else '否'}")

        if 'note' in task:
            logger.info(f"📝 備註: {task['note']}")

        if not task['execute']:
            continue

        # SSH 連線資訊
        ssh_info = task.get('ssh', {})
        if ssh_info.get('enable', False):
            logger.info("🌐 SSH 連線設定：")
            logger.info(f"  - 狀態: ✅ 啟用")
            logger.info(f"  - 主機: {ssh_info.get('host')}")
            logger.info(f"  - 埠號: {ssh_info.get('port', 22)}")
            logger.info(f"  - 使用者: {ssh_info.get('username')}")
            if ssh_info.get('use_key'):
                logger.info(f"  - 驗證方式: 🔑 私鑰登入 ({ssh_info.get('key_path', '未設定 key_path')})")
            else:
                logger.info(f"  - 驗證方式: 🔐 密碼登入")
        else:
            logger.info("🌐 SSH 連線設定：未啟用")

        # dump 說明
        logger.info("📤 匯出 (Dump):")
        if "dump" not in task["action"]:
            logger.info("  ❗ 未設定 dump 動作")
        else:
            dump = task['action']['dump']

            host = dump.get('host')
            port = dump.get('port')
            dir_path = os.path.join(OUTPUT_DIR, dump.get('hostname', socket.gethostname()), datetime.now().__format__('%Y%m%d'))
            logger.info(f"  - 目標主機: {host}:{port}")
            logger.info(f"  - 目標目錄: {dir_path}")

            if dump.get("items"):
                for item in dump["items"]:
                    db = item.get("database")
                    cols = item.get("collections", [])

                    dump_collections.setdefault(db, []).extend(cols)

                    if db and cols:
                        logger.info(f"  - 資料庫: {db}")
                        if len(cols) == 1 and cols[0] == "*":
                            logger.info(f"    匯出集合: 所有集合 (*)")
                        else:
                            logger.info(f"    匯出集合: {', '.join(cols)}")
                    else:
                        logger.info("  ❗ 資料庫名稱或集合為空，請檢查 dump 設定")
            else:
                logger.info("  ❗ 未設定任何要匯出的資料庫或集合")

        # restore 說明
        logger.info("📥 還原 (Restore):")
        if "restore" not in task["action"]:
            logger.info("  ❗ 未設定 restore 動作")
        else:
            restore = task["action"]["restore"]
            logger.info(f"  - 還原日期: {restore.get('date', '未設定')}")
            logger.info(
                f"  - 是否刪除原集合: {'是' if restore.get('drop_collection') else '否'}")
            logger.info(
                f"  - 是否清空文件再導入: {'是' if restore.get('clear_doc') else '否'}")
            logger.info(
                f"  - 是否附加日期欄位: {'是' if restore.get('attach_date') else '否'}")

            host = restore.get('host')
            port = restore.get('port')

            logger.info(f"  - 目標主機: {host}:{port}")

            dir_path = os.path.join(OUTPUT_DIR, restore.get('hostname', socket.gethostname()))

            if restore.get("items"):
                for item in restore["items"]:
                    db = item.get("database")
                    cols = item.get("collections", [])

                    if db and cols:
                        logger.info(f"  - 資料庫: {db}")
                        if len(cols) == 1 and cols[0] == "*":
                            logger.info(f"    還原集合: 所有集合 (*)")
                        else:
                            logger.info(f"    還原集合: {', '.join(cols)}")

                        if restore.get('date'):
                            logger.info(f"    指定日期: {restore.get('date')}")
                        else:
                            lastst_date_dir = get_lastst_date(dir_path)
                            if lastst_date_dir:
                                logger.info(f"    未指定日期，將使用最新的備份資料夾 {lastst_date_dir}")
                            else:
                                logger.info(f"    未指定日期，且無可用的備份資料夾，先執行匯出。")
                    else:
                        logger.info("  ❗ 資料庫名稱或集合為空，請檢查 restore 設定")
            else:
                logger.info("  ❗ 未設定任何要還原的資料庫或集合")

        # random 說明
        logger.info("🎲 隨機抽樣/重新命名 (Random):")
        random = task["action"].get("random", {})
        if not random:
            logger.info("  ❗ 未設定 random 內容")
        else:
            for db_name, collections in random.items():
                if not collections:
                    logger.info(f"  - 資料庫: {db_name} ❗ 無任何集合設定")
                    continue
                logger.info(f"  - 資料庫: {db_name}")
                for old_name, info in collections.items():
                    new_name = info.get("name")
                    amount = info.get("amount")
                    if not new_name:
                        logger.info(f"    集合「{old_name}」 ❗ 未設定新名稱")
                    else:
                        logger.info(f"    集合「{old_name}」 → 新名稱: 「{new_name}」")
                    if amount:
                        logger.info(f"      抽樣數量: {amount}")
                    else:
                        logger.info("      （未設定抽樣數量，預設導入全部）")

        # size 說明
        logger.info("📏 資料庫/集合大小 (Size):")
        if "size" not in task["action"]:
            logger.info("  ❗ 未設定 size 動作")
        else:
            size = task["action"]["size"]

            host = size.get('host')
            port = size.get('port')
            dir_path = os.path.join(OUTPUT_DIR, size.get('hostname', socket.gethostname()))
            logger.info(f"  - 目標主機: {host}:{port}")
            logger.info(f"  - 參考目錄: {dir_path}")

            if size.get("items"):
                for item in size["items"]:
                    db = item.get("database")
                    cols = item.get("collections", [])

                    if db and cols:
                        logger.info(f"  - 資料庫: {db}")
                        if len(cols) == 1 and cols[0] == "*":
                            logger.info(f"    檢查集合大小: 所有集合 (*)")
                        else:
                            logger.info(f"    檢查集合大小: {', '.join(cols)}")
                    else:
                        logger.info("  ❗ 資料庫名稱或集合為空，請檢查 size 設定")
            else:
                logger.info("  ❗ 未設定任何要檢查大小的資料庫或集合")

    logger.info(f"===================")


def wait_for_user_confirmation():
    while True:
        choice = input("🟡 是否繼續執行？(Y/N，預設為 N)：").strip().lower()
        if choice == "y":
            print("✅ 繼續執行...\n")
            break
        elif choice == "n" or choice == "":
            print("🛑 使用者選擇中斷，程式終止。")
            exit(0)
        else:
            print("⚠️ 無效輸入，請輸入 Y 或 N（Enter 預設為 N）。")


def human_time(seconds: float) -> str:
    """將秒數轉成 hh:mm:ss"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
