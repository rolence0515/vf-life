# Cloud SQL 備份/還原工具使用說明

本工具 `cloudsql_bk_tool.sh` 提供 Google Cloud SQL（PostgreSQL）資料庫的備份與還原操作，支援 uat 及 prod 兩個環境，並以互動式流程協助你安全執行。

---

## 使用前準備

1. 請先安裝並設定好 [gcloud CLI](https://cloud.google.com/sdk/docs/install)。
2. 確認你有 Cloud SQL 實例的操作權限。
3. 請將本工具放在專案目錄下，並給予執行權限：

```sh
chmod +x cloudsql_bk_tool.sh
```

---

## 執行方式

```sh
./cloudsql_bk_tool.sh uat   # 操作 UAT 環境
./cloudsql_bk_tool.sh prod  # 操作 PROD 環境
```

---

## 操作流程

1. 執行腳本後，會先讓你選擇「備份」或「還原」。
2. 顯示目前選擇的 GCP 專案、環境、Cloud SQL 實例、資料庫名稱與操作類型，請再次確認。
3. 輸入 `y` 確認後才會繼續。
4. 
   - **備份**：
     - 會自動呼叫 `gcloud sql backups create` 建立備份。
     - 執行結果會顯示成功或失敗。
   - **還原**：
     - 會先列出所有可用備份（`gcloud sql backups list`）。
     - 輸入欲還原的 BACKUP_ID。
     - 會自動呼叫 `gcloud sql backups restore` 進行還原。
     - 執行結果會顯示成功或失敗。

---

## 注意事項

- 備份與還原皆為整個 Cloud SQL 實例層級操作，請務必小心。
- 還原作業會覆蓋現有資料，請務必確認 BACKUP_ID 與環境無誤。
- 若遇權限或網路問題，請依錯誤訊息排查。
- 建議於非高峰時段執行還原作業。

---

## 常見指令範例

- 建立備份：
  ```sh
  gcloud sql backups create --instance=INSTANCE_NAME --project=PROJECT_ID
  ```
- 查詢備份：
  ```sh
  gcloud sql backups list --instance=INSTANCE_NAME --project=PROJECT_ID
  ```
- 還原備份：
  ```sh
  gcloud sql backups restore BACKUP_ID --restore-instance=INSTANCE_NAME --project=PROJECT_ID
  ```

---

如有問題請聯絡系統管理員。
