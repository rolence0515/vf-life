# Cloud Run Service DNS 設定指南

## 1. 確認 Cloud Run Service 的 URL
1. 登錄到 [Google Cloud Console](https://console.cloud.google.com)。
2. 確保您選擇了正確的專案。
3. 前往 **Cloud Run**，找到 `vf-life-prod` 服務。
4. 記下該服務的 URL，例如：`https://vf-life-prod-548835227059.asia-east2.run.app`

---

## 2. 添加自定義域名
1. 在 Google Cloud Console 中，導航到 **Cloud Run**。
2. 點擊 `vf-life-prod` 服務。
3. 點擊 **管理自定義域名**。
4. 點擊 **添加自定義域名**。
5. 輸入您希望綁定的域名，例如：`app.violetflames.com`。
6. 選擇對應的域名（如果尚未驗證域名，請先完成域名驗證）。

---

## 3. 獲取 DNS 記錄
1. 完成自定義域名添加後，Google Cloud 會提供需要添加到 DNS 的記錄，例如：
   - **CNAME 記錄**：
     ```
     主機名: app
     值: ghs.googlehosted.com
     ```

---

## 4. 在 DNS 提供商中添加記錄
1. 登錄到您的 DNS 提供商（例如 Cloudflare、Google Domains）。
2. 添加以下 DNS 記錄：
   - **CNAME 記錄**：
     ```
     主機名: app
     值: ghs.googlehosted.com
     TTL: 自動
     ```
3. 保存更改。

---

## 5. 驗證 DNS 設定
1. 返回 Google Cloud Console 的 **Cloud Run** 頁面。
2. 點擊 `vf-life-prod` 服務。
3. 驗證自定義域名是否已正確綁定。
4. 使用瀏覽器訪問 `https://app.violetflames.com`，確認服務是否正常運行。

---

## 6. 注意事項
- 確保 DNS 記錄的 TTL 設置為自動或較短的時間，以便快速生效。
- 如果使用 HTTPS，請確保 Cloud Run 已自動為自定義域名配置 SSL 證書。
- 如果遇到問題，請聯繫 Google Cloud 支持或您的 DNS 提供商。

---

完成以上步驟後，您的 Cloud Run Service 應該已成功綁定到自定義域名。