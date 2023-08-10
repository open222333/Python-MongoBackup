# Python-MongoDBBackup

```
測試資料處理
還原mongodb測試資料環境小工具
```

# backup.py - 批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行

```json
// conf/mongo.json
[
  {
    "execute": true, // 是否執行
    "action": {
      "dump": false, // 匯出
      "restore": false // 匯入 以最新日期進行匯入
    },
    "host": "127.0.0.1:27017",
	"hostname": null, // 若未指定 則顯示本機
    "items": [
      {
        "database": "database1",
        "collections": [
          "collection_1",
          "collection_2"
        ]
      },
      {
        "database": "database2",
        "collections": [
          "collection_1",
          "collection_2"
        ]
      }
    ]
  }
]
```

```bash
usage: backup.py [-h] [-d] [-r] [--date DATE] [--drop_collection]
                 [--clear_doc] [--attach_date]

批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行

optional arguments:
  -h, --help         show this help message and exit

功能:
  可使用json設置是否使用以下功能

  -d, --dump         匯出
  -r, --restore      匯入

匯入附加功能:
  匯入時使用

  --date DATE        日期
  --drop_collection  刪除目前集合
  --clear_doc        清除collection內文檔
  --attach_date      集合名稱附加日期
```

# data.py - 建立測試用資料庫 隨機取得資料

```bash
usage: data.py [-h] [-H HOST] [-d DATABASE] [-c COLLECTION]
               [--new_collection NEW_COLLECTION] [-r RANDOM] [--json]
               [--remove_id]

建立測試用資料庫 隨機取得資料

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  主機
  -d DATABASE, --database DATABASE
                        目標資料庫
  -c COLLECTION, --collection COLLECTION
                        目標集合
  --new_collection NEW_COLLECTION
                        隨機建立的集合名稱
  -r RANDOM, --random RANDOM
                        匯入指定數量到集合
  --json                根據 mongo.json 執行, 其餘參數將被忽略
  --remove_id           移除原有_id, 隨機資料建立新_id
```
