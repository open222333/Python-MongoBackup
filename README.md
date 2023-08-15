# Python-MongoDBBackup

```
測試資料處理
還原mongodb測試資料環境小工具
```

# mongo.json 說明

```json
// conf/mongo.json
[
  {
    "execute": true, // 是否執行
    "host": "",
    "action": {
      "dump": {
		// 匯出 相關設定
        "execute": false, // 是否執行
		"hostname": "", // 若未指定 則顯示本機
        "items": [	// 指定 資料庫 集合
          {
            "database": "database1",
            "collections": [
              "collection1"
            ]
          }
        ]
      },
      "restore": {
		// 匯入 相關設定
        "execute": false,
		"hostname": "", // 若未指定 則顯示本機
        "date": "20230101", // 匯入指定日期(需存在)的備份檔
		"drop_collection": false, // 匯入同時刪除目前同名稱集合
        "clear_doc": false, // 匯入同時清除collection內所有文檔
        "attach_date": false, // 匯入時 集合名稱附加日期
        "items": [
          {
            "database": "database1",
            "collections": [
              "collection1"
            ]
          }
        ]
      },
      "random": {
		// 隨機資料 根據 old_collection_name1 建立 new_collection_name1
        "database_name": {
          "old_collection_name1": {
            "name": "new_collection_name1",
            "amount": null
          }
        }
      }
    }
  }
]
```

# backup.py - 批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行

```bash
usage: backup.py [-h]

批量mongodb備份 - 匯出匯入 預設根據 conf/mongo.json 設定執行
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
