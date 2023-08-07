# Python-MongoDBBackup

測試資料處理
還原mongodb測試資料環境小工具

## json檔設置解說

```json
[
  {
    "execute": true, // 是否執行
    "dump": true, // 匯出
    "restore": true, // 匯入 以最新日期進行匯入
    "host": "",
    "database": "",
    "collections": ""
  },
  {
    "execute": true,
    "dump": true,
    "restore": true,
    "host": "",
    "database": "",
    "collections": ""
  }
]
```
