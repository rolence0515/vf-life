# README: 如何使用 deploy_cloudrun_v2.sh 部署到 Cloud Run（Artifact Registry 版本）

## 概述
`deploy_cloudrun_v2.sh` 是用於將應用程式部署到 Google Cloud Run 的腳本，與 v1 版本不同，v2 會在本地建置 Docker 映像並推送到 Google Artifact Registry，而非使用 Cloud Build 遠端建置與推送到 GCR（Google Container Registry）。

---

## 主要差異
- **v1 (`deploy_cloudrun.sh`)**：
  - 使用 `gcloud builds submit` 遠端建置 Docker 映像。
  - 推送映像到 GCR（gcr.io）。
- **v2 (`deploy_cloudrun_v2.sh`)**：
  - 在本地執行 `docker build` 建置映像。
  - 推送映像到 Artifact Registry（`asia-east1-docker.pkg.dev` 這類路徑）。
  - 部署前會自動檢查並啟動 Colima（適用於 macOS 開發環境）。

---

## 先決條件
1. **已安裝工具**：
   - Google Cloud CLI
   - Docker
   - Colima（macOS 用於本地 Docker 執行環境）
2. **Google Cloud 設定**：
   - 已登入 (`gcloud auth login`)
   - 已設定專案 (`gcloud config set project <PROJECT_ID>`)
   - Artifact Registry 已建立並啟用對應權限
3. **環境變數檔案**：
   - `.env.uat`、`.env.prod` 於專案根目錄

---

## 使用方式

### 1. 執行腳本
```bash
./deploy_cloudrun_v2.sh <環境>
```
- `<環境>`：`uat` 或 `prod`

### 2. 範例
- 部署到 UAT：
  ```bash
  ./deploy_cloudrun_v2.sh uat
  ```
- 部署到 Production：
  ```bash
  ./deploy_cloudrun_v2.sh prod
  ```

---

## 腳本功能
1. **自動檢查 Colima 狀態**：
   - 若 Colima 未啟動會自動啟動，確保本地 Docker 可用。
2. **本地建置 Docker 映像**：
   - 使用 `docker build`，並以指定名稱與 tag 標記。
3. **推送映像到 Artifact Registry**：
   - 登入並推送映像到 Google Artifact Registry。
4. **部署到 Cloud Run**：
   - 使用 gcloud 指令部署，並自動帶入環境變數。

---

## 注意事項
- 請確保 Colima、Docker、gcloud 均已安裝並設定完成。
- `.env.uat`、`.env.prod` 必須存在且內容正確。
- 若 Artifact Registry 尚未建立，請先於 GCP Console 建立對應倉庫。
- 若遇到權限問題，請確認 Artifact Registry 權限與 gcloud 登入帳號。

---

## 常見問題

### Q: Colima 是什麼？為什麼需要？
A: Colima 是 macOS 上的輕量級本地 Docker 執行環境，適合 Apple Silicon/M1/M2。腳本會自動檢查並啟動 Colima，確保本地建置映像順利。

### Q: Artifact Registry 跟 GCR 有什麼不同？
A: Artifact Registry 是 Google Cloud 推薦的新一代映像倉庫，支援多區域、IAM 權限控管，建議新專案使用。

### Q: 如何檢查部署結果？
A: 腳本執行完畢後會顯示部署狀態，也可用：
```bash
gcloud run services describe <SERVICE_NAME> --region=<REGION>
```

---

## 聯絡方式
如有問題請聯絡開發團隊或參考專案文件。
