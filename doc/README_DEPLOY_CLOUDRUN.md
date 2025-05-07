# README: 如何使用 deploy_cloudrun.sh 部署到 Cloud Run

## 概述
`deploy_cloudrun.sh` 是一個用於將應用程式部署到 Google Cloud Run 的腳本。此腳本支援多環境部署（如 UAT 和 Production），並使用標準的 `.env` 檔案來管理環境變數。

---

## 先決條件
在使用此腳本之前，請確保已完成以下準備工作：

### 1. 安裝必要工具
- **Google Cloud CLI**: [安裝指南](https://cloud.google.com/sdk/docs/install)
- **Docker**: [安裝指南](https://docs.docker.com/get-docker/)

### 2. 設定 Google Cloud 環境
- 登入 Google Cloud：
  ```bash
  gcloud auth login
  ```
- 設定專案：
  ```bash
  gcloud config set project <PROJECT_ID>
  ```

### 3. 建立環境變數檔案
在專案目錄下建立以下 `.env` 檔案：
- `.env.uat`：用於 UAT 環境
- `.env.prod`：用於 Production 環境

每個檔案應包含應用程式所需的環境變數，例如：
```env
KEY1=value1
KEY2=value2
```

---

## 使用方式

### 1. 執行腳本
使用以下指令來部署應用程式：
```bash
./deploy_cloudrun.sh <環境>
```
- `<環境>` 可為 `uat` 或 `prod`。

### 2. 範例
- 部署到 UAT 環境：
  ```bash
  ./deploy_cloudrun.sh uat
  ```
- 部署到 Production 環境：
  ```bash
  ./deploy_cloudrun.sh prod
  ```

---

## 腳本功能
1. **建置 Docker 映像**：
   腳本會自動建置 Docker 映像並推送到 Google Container Registry。

2. **部署到 Cloud Run**：
   腳本會根據指定的環境，將應用程式部署到 Cloud Run。

3. **環境變數管理**：
   使用 `.env` 檔案來設定應用程式的環境變數。

4. **多環境支援**：
   支援 UAT 和 Production 環境，並根據環境自動設定服務名稱和其他參數。

---

## 注意事項
1. 確保 `.env.uat` 和 `.env.prod` 檔案已正確配置，並包含應用程式所需的所有環境變數。
2. 部署過程中，腳本會自動檢查錯誤並提供詳細的錯誤訊息。
3. 如果需要新增其他環境，請修改腳本中的環境邏輯。

---

## 常見問題

### Q: 如何檢查部署是否成功？
A: 腳本執行完成後，會自動顯示 Cloud Run 服務的詳細資訊。您也可以使用以下指令檢查服務狀態：
```bash
gcloud run services describe <SERVICE_NAME> --region=<REGION>
```

### Q: 如果部署失敗，該怎麼辦？
A: 請檢查腳本輸出的錯誤訊息，並確認以下事項：
- `.env` 檔案是否正確配置。
- Google Cloud CLI 是否已正確安裝並設定。
- Docker 映像是否成功建置並推送到 Container Registry。

### Q: 如何查看部署後的日誌？
A: 您可以使用以下指令查看 Cloud Run 的日誌：
```bash
gcloud run services logs read vf-life-uat --project="rolence-project" --region="asia-east2" --limit=100
```
請將 `<SERVICE_NAME>` 替換為您的服務名稱，例如 `vf-life-uat` 或 `vf-life-prod`。

---

## 聯絡方式
如有任何問題，請聯絡開發團隊或參考專案文件。