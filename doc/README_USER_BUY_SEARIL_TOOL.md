# USER_BUY_SERIAL_TOOL 使用說明

## 工具簡介

`user_buy_serial_tool.py` 是一個用於批次匯入會員購買影片系列(csv)資料，並自動建立/查詢會員、開通會員可觀看影片權限的工具。適用於根據購買紀錄自動管理會員與影片觀看權限。

---

## CSV 檔案格式

- 檔名範例：`USER_BUY_SERIAL_SAMPLE.csv`
- 檔案需有 header，格式如下：

```
email,serial1,serial2
user1@example.com,1,0
user2@example.com,1,1
...（多筆資料）
```
- `serial1` 代表購買上半場（series_id=1），`serial2` 代表購買下半場（series_id=2）
- `email` 為會員帳號

---

## 資料庫操作說明

### 1. user 表
- 若 email 不存在，則新增 user，密碼為 email 做 sha256 雜湊後取前 6 碼（參考 README_DB 說明）
- 若 email 已存在，則不異動 user 表
- 需記錄 user_id 供後續使用

### 2. user_videos 表
- 依據 csv 中 serial1/serial2 欄位值為 1，查詢 series_id=1/2 關聯的所有 videos
- 將這些 videos 以 user_id 寫入 user_videos 表，代表開通觀看權限
- 若 user_videos 已有相同 user_id, video_id，不重複寫入

---

## 執行結果輸出

- 產生一份結果 csv，欄位如下：
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

| email              | serial1 | serial2 |
|--------------------|---------|---------|
| user1@example.com  | 1       | 0       |
| user2@example.com  | 1       | 1       |
| user3@example.com  | 0       | 1       |

執行後產生結果 csv：

| email              | user_id | new_user | default_pw | videos_count |
|--------------------|---------|----------|------------|--------------|
| user1@example.com  | 101     | 1        | ab12cd     | 3            |
| user2@example.com  | 102     | 0        |            | 2            |
| user3@example.com  | 103     | 1        | 34ef56     | 1            |

---

如有問題請聯絡開發人員。
