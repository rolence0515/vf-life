# USER_BUY_SERIAL_TOOL 使用說明

## 工具簡介

`user_buy_serial_tool.py` 是一個用於批次匯入會員購買影片系列(csv)資料，並自動建立/查詢會員、開通會員可觀看影片權限的工具。適用於根據購買紀錄自動管理會員與影片觀看權限。

---

## 執行環境參數說明

本工具支援多種執行環境，請於執行時以第一個參數指定環境名稱：
- dev：開發環境
- uat：測試環境
- prod：正式環境

執行範例：
```
python user_buy_serial_tool.py uat yourfile.csv
```

工具會自動載入對應的 `.env.dev`、`.env.uat` 或 `.env.prod` 檔案，並將內容設為環境變數。載入後會顯示所有環境變數內容，請使用者確認無誤後輸入 y 才會繼續執行。

---

## CSV 檔案格式

- 檔名範例：`USER_BUY_SERIAL_SAMPLE.csv`
- 檔案需有 header，格式如下：

```
name,email,serial1,serial2
王小明,user1@example.com,1,0
李小華,user2@example.com,1,1
...（多筆資料）
```
- `name` 為會員姓名
- `email` 為會員帳號
- `serial1` 代表購買上半場（series_id=1），`serial2` 代表購買下半場（series_id=2）

---

## 資料庫操作說明

### 1. user 表
- 若 email 不存在，則新增 user，**同時寫入 name 欄位**，密碼為 email 做 sha256 雜湊後取前 6 碼（參考 README_DB 說明）
- 若 email 已存在，則不異動 user 表
- 需記錄 user_id 供後續使用

### 2. user_videos 表
- 依據 csv 中 serial1/serial2 欄位值為 1，查詢 series_id=1/2 關聯的所有 videos
- 將這些 videos 以 user_id 寫入 user_videos 表，代表開通觀看權限
- 若 user_videos 已有相同 user_id, video_id，不重複寫入
- 若 serial1/serial2 欄位值為 0，且 user_videos 表中已存在相應的 user_id 和 series_id=1/2 關聯的 videos，則刪除這些 video 的觀看權限

---

## 執行結果輸出

- 產生一份結果 csv，欄位如下：
  - name
  - email
  - user_id
  - new_user（1=新建，0=已存在）
  - default_pw（新建使用者才有預設密碼，否則空白）
  - videos_count（本次開通影片數量）

---

## 執行流程

1. 讀取輸入 csv 檔
2. 依序處理每一筆 email：
   - 檢查 user 是否存在，若否則建立（密碼規則見上）
   - 依 serial1/serial2 欄位，查詢對應 series 的所有 videos
   - 寫入 user_videos（避免重複）
   - 統計本次開通影片數
3. 輸出結果 csv

---

## 依賴
- Python 3
- 需能連線至專案資料庫
- 需有 psycopg2 或 SQLAlchemy 等資料庫套件

---

## 注意事項
- 請先備份資料庫
- 輸入 csv 檔案請確認格式正確
- 執行前請確認資料庫連線資訊正確

---

## 範例

| name   | email              | serial1 | serial2 |
|--------|--------------------|---------|---------|
| 王小明 | user1@example.com  | 1       | 0       |
| 李小華 | user2@example.com  | 1       | 1       |
| ...    | ...                | ...     | ...     |

執行後產生結果 csv：

| name   | email              | user_id | new_user | default_pw | videos_count |
|--------|--------------------|---------|----------|------------|--------------|
| 王小明 | user1@example.com  | 101     | 1        | ab12cd     | 3            |
| 李小華 | user2@example.com  | 102     | 0        |            | 2            |
| ...    | ...                | ...     | ...      | ...        | ...          |

---

如有問題請聯絡開發人員。
