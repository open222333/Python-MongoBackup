# Python-MongoBackup

```
測試資料處理
還原 MongoDB 測試資料環境小工具
```

---

## 目錄

- [專案說明](#專案說明)
- [設定檔說明](#設定檔說明)
  - [config.ini](#configini)
  - [mongo.json](#mongojson)
- [各模式說明](#各模式說明)
  - [dump - 匯出](#dump---匯出)
  - [restore - 匯入](#restore---匯入)
  - [size - 查看大小](#size---查看大小)
  - [random - 隨機資料](#random---隨機資料)
- [執行流程](#執行流程)
  - [backup.py 流程](#backuppy-流程)
  - [data.py 流程](#datapy-流程)
- [使用方法](#使用方法)
  - [backup.py](#backuppy)
  - [data.py](#datapy)
- [SSH 通道支援](#ssh-通道支援)
- [建議注意事項](#建議注意事項)

---

## 專案說明

提供 MongoDB 資料的**匯出 (dump)**、**匯入 (restore)**、**大小查詢 (size)**，以及**隨機測試資料建立 (random)** 功能，適用於測試環境資料準備與還原。

---

## 設定檔說明

### config.ini

從 `conf/config.ini.default` 複製並調整：

```ini
[LOG]
; 關閉 log 功能，輸入 true / True / 1，預設不關閉
; LOG_DISABLE=1

; logs 路徑，預設 logs/
; LOG_PATH=

; 關閉紀錄 log 檔案，輸入 true / True / 1，預設不關閉
; LOG_FILE_DISABLE=1

; 設定 log 等級 DEBUG / INFO / WARNING / ERROR / CRITICAL，預設 WARNING
; LOG_LEVEL=

[SETTING]
; 設定 json 設定檔路徑，預設 conf/mongo.json
; JSON_PATH=

; 設定備份檔案存放資料夾，預設 output/
; OUTPUT_DIR=
```

### mongo.json

從 `conf/mongo.json.default` 複製並調整，支援多組設定（陣列）：

```json
[
  {
    // 是否執行此組設定
    "execute": true,
    // 備註（選填）
    "note": "備註說明",
    // SSH 通道設定（選填，不使用可移除）
    "ssh": {
      "enable": true,
      "host": "remote_host_ip_or_domain",
      "port": 22,
      "username": "ssh_user",
      "password": "ssh_password",
      "key_path": "/path/to/private_key",
      "use_key": false
    },
    "action": {
      // 依需求加入 dump / restore / size / random
    }
  }
]
```

> 同一組設定可同時包含多個 action（如同時執行 dump 與 restore），各 action 說明如下。

---

## 各模式說明

### dump - 匯出

將 MongoDB 集合匯出至本機備份目錄（`output/<hostname>/`）。

```json
"dump": {
  "host": "127.0.0.1",      // 來源主機，預設 127.0.0.1
  "port": "27017",           // 埠號，預設 27017
  "username": null,          // 認證帳號（無認證可省略）
  "password": null,          // 認證密碼
  "auth_database": "admin",  // 認證資料庫，預設 admin
  "hostname": null,          // 備份子目錄名稱，預設取本機 hostname
  "items": [
    {
      "database": "your_db",
      "collections": ["col1", "col2"]
      // 使用 ["*"] 可匯出整個資料庫所有集合
    }
  ]
}
```

**備份輸出路徑格式：**
```
output/<hostname>/<date>/<database>/<collection>.bson
```

---

### restore - 匯入

將備份檔案還原至指定 MongoDB。

```json
"restore": {
  "host": "127.0.0.1",        // 目標主機，預設 127.0.0.1
  "port": "27017",             // 埠號，預設 27017
  "username": null,            // 認證帳號
  "password": null,            // 認證密碼
  "auth_database": "admin",    // 認證資料庫
  "hostname": "",              // 指定讀取哪個主機的備份資料（對應備份子目錄）
  "date": "20230101",          // 指定還原哪一天的備份（需存在）
  "drop_collection": false,    // 匯入前先刪除同名集合
  "clear_doc": false,          // 匯入後清除集合內所有文件
  "attach_date": false,        // 集合名稱附加日期後綴（如 col1_20230101）
  "items": [
    {
      "database": "your_db",
      "collections": ["col1", "col2"],
      // dirpath: 指定備份資料夾路徑，可替代 collections
      //          自動解析資料夾結構產生可匯入的集合清單
      "dirpath": ""
    }
  ]
}
```

**`drop_collection` vs `clear_doc` 差異：**

| 選項 | 行為 |
|------|------|
| `drop_collection: true` | 匯入前刪除整個集合（含索引） |
| `clear_doc: true` | 匯入後刪除集合內所有文件（保留結構） |

---

### size - 查看大小

查詢指定集合的資料大小（MB）。

```json
"size": {
  "host": "127.0.0.1",
  "port": "27017",
  "username": null,
  "password": null,
  "auth_database": "admin",
  "hostname": null,
  "items": [
    {
      "database": "your_db",
      "collections": ["col1"]
      // 使用 ["*"] 查詢整個資料庫所有集合大小
    }
  ]
}
```

結果輸出範例：
```
your_db.col1 大小: 12.34 MB
```

---

### random - 隨機資料

用於 `data.py`，根據現有集合隨機取樣建立新的測試集合。

```json
"random": {
  "database_name": {
    "old_collection_name1": {
      "name": "new_collection_name1",  // 新集合名稱
      "amount": null                   // 取樣數量，null 使用預設 200 筆
    }
  }
}
```

---

## 執行流程

### backup.py 流程

```
讀取 conf/mongo.json（或指定 -j 路徑）
        │
        ▼
列印設定內容，等待使用者確認（Enter 繼續）
        │
        ▼
依序處理每組設定（execute: true 才執行）
        │
        ├─► [dump]    連線來源 MongoDB（支援 SSH 通道）
        │             逐一匯出指定集合 → output/<hostname>/<date>/
        │
        ├─► [restore] 連線目標 MongoDB（支援 SSH 通道）
        │             依指定日期讀取備份 → 逐一還原集合
        │
        └─► [size]    連線 MongoDB（支援 SSH 通道）
                      逐一查詢集合大小並輸出
        │
        ▼
輸出執行時間（秒 / 可讀格式）
```

### data.py 流程

**命令列模式（預設）：**
```
解析參數（host / database / collection / new_collection / random）
        │
        ▼
連線 MongoDB，從指定集合隨機取樣
        │
        ▼
逐筆寫入新集合（含進度條顯示）
```

**JSON 模式（`--json`）：**
```
讀取 conf/mongo.json
        │
        ▼
對每組 execute: true 的設定，讀取 action.random
        │
        ▼
多執行緒同時執行各集合的隨機取樣與寫入
```

---

## 使用方法

### backup.py

```bash
# 使用預設設定檔 conf/mongo.json
python backup.py

# 指定自訂設定檔路徑
python backup.py -j /path/to/custom.json
```

```
usage: backup.py [-h] [-j JSON_PATH]

批量 MongoDB 備份 - 匯出匯入，預設根據 conf/mongo.json 設定執行

optional arguments:
  -h, --help            顯示說明
  -j, --json_path       指定 json 設定檔路徑，預設 conf/mongo.json
```

**範例：只執行 dump（匯出）**

```json
// conf/mongo.json
[
  {
    "execute": true,
    "action": {
      "dump": {
        "host": "127.0.0.1",
        "port": "27017",
        "items": [
          { "database": "mydb", "collections": ["users", "orders"] }
        ]
      }
    }
  }
]
```

**範例：只執行 restore（匯入）**

```json
[
  {
    "execute": true,
    "action": {
      "restore": {
        "hostname": "my-server",
        "date": "20240508",
        "drop_collection": true,
        "items": [
          { "database": "mydb", "collections": ["users", "orders"] }
        ]
      }
    }
  }
]
```

---

### data.py

```bash
# 命令列模式：從 mydb.users 隨機取 500 筆，寫入 mydb.random_users
python data.py -H 127.0.0.1 -d mydb -c users -r 500

# 指定新集合名稱
python data.py -H 127.0.0.1 -d mydb -c users --new_collection test_users -r 100

# 移除原有 _id，讓 MongoDB 自動產生新 _id
python data.py -H 127.0.0.1 -d mydb -c users --remove_id -r 100

# 根據 mongo.json 執行（多執行緒）
python data.py --json
```

```
usage: data.py [-h] [-H HOST] [-d DATABASE] [-c COLLECTION]
               [--new_collection NEW_COLLECTION] [-r RANDOM] [--json]
               [--remove_id]

optional arguments:
  -h, --help                        顯示說明
  -H HOST, --host HOST              主機
  -d DATABASE, --database DATABASE  目標資料庫
  -c COLLECTION, --collection COLLECTION
                                    目標集合（取樣來源）
  --new_collection NEW_COLLECTION   隨機建立的集合名稱，預設 random_<collection>
  -r RANDOM, --random RANDOM        取樣數量，預設 200
  --json                            根據 mongo.json 執行，其餘參數忽略
  --remove_id                       移除原有 _id，建立新 _id
```

---

## SSH 通道支援

`backup.py` 支援透過 SSH 通道連接遠端 MongoDB，適用於無法直接連線的環境。

```json
"ssh": {
  "enable": true,
  "host": "remote_host_ip_or_domain",
  "port": 22,
  "username": "ssh_user",
  "password": "ssh_password",
  "key_path": "/path/to/private_key",
  "use_key": false   // true 時使用 key_path，false 時使用 password
}
```

> SSH 通道建立後，本地會自動綁定一個臨時埠號進行轉發，操作完成後自動關閉。

---

## 建議注意事項

### 設定與環境

- 首次使用請複製 `conf/mongo.json.default` → `conf/mongo.json`，以及 `conf/config.ini.default` → `conf/config.ini`
- 多組設定同時執行時，**依陣列順序**依序處理，請注意設定順序
- `"execute": false` 的設定組會被跳過，可用於暫時停用而不需刪除設定

### dump（匯出）

- `hostname` 建議明確填寫，避免因主機名稱不同導致還原時找不到備份目錄
- 使用 `["*"]` 匯出所有集合前，請確認資料庫規模，避免意外匯出大量資料
- 備份輸出目錄預設為 `output/`，請確認磁碟空間充足

### restore（匯入）

- **`drop_collection: true`** 會在匯入前永久刪除集合（含索引），操作前請確認目標環境
- `date` 欄位指定的備份日期必須存在於 `output/<hostname>/` 目錄中，否則會失敗
- `attach_date: true` 會將集合命名為 `<collection>_<date>`，可避免覆蓋現有資料
- 使用 `dirpath` 替代 `collections` 時，請確認路徑結構符合匯出格式

### SSH 通道

- 使用 SSH 金鑰時，請將 `use_key` 設為 `true` 並確認 `key_path` 存在且有讀取權限
- SSH 密碼明文儲存在 JSON 設定檔中，請注意設定檔的存取權限，不應提交至版本控制

### data.py（隨機資料）

- `--json` 模式使用多執行緒，大量寫入時請注意 MongoDB 連線數上限
- `--remove_id` 用於避免 `_id` 衝突，若目標集合已有相同 `_id` 的文件，不使用此選項可能導致寫入失敗
- 每筆資料插入間隔 1 秒（`sleep(1)`），大量資料時執行時間較長

### 一般建議

- 在正式環境執行前，先在測試環境驗證設定正確
- 執行前會顯示設定內容並等待確認，請仔細核對後再按 Enter 繼續
- Log 檔案預設存放於 `logs/`，可透過 `config.ini` 調整等級或關閉
