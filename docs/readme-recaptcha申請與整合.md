# Google reCAPTCHA 申請與整合指南

本文件說明如何申請 Google reCAPTCHA（以 v2 為例），並取得 Site Key 及 Secret Key，供網站前後端整合使用。

---

## 1. 前往 Google reCAPTCHA 管理平台

網址：https://www.google.com/recaptcha/admin/create

---

## 2. 註冊新網站

1. 登入 Google 帳號。
2. 點選「+」註冊新網站。
3. 填寫下列資訊：
   - **標籤**：自訂名稱（如：vf-life-login）
   - **reCAPTCHA 類型**：
     - 建議選擇「reCAPTCHA v2」>「我不是機器人」勾選框
   - **網域**：輸入你的網站網域（如：example.com，若本地測試可填 localhost）
   - **擁有者**：預設為你的 Google 帳號
   - 勾選同意 reCAPTCHA 條款
4. 點選「送出」

---

## 3. 取得金鑰

註冊完成後，會看到：
- **Site Key**：給前端用
- **Secret Key**：給後端驗證用（請勿外洩）

---

## 4. 前端整合

在登入頁表單內適當位置加入：

```html
<div class="g-recaptcha" data-sitekey="你的 Site Key"></div>
<script src="https://www.google.com/recaptcha/api.js" async defer></script>
```

---

## 5. 後端驗證（Python Flask 範例）

```python
import requests

recaptcha_token = request.form.get('g-recaptcha-response')
if not recaptcha_token:
    # 請提示用戶完成驗證
    ...
verify_url = 'https://www.google.com/recaptcha/api/siteverify'
data = {
    'secret': '你的 Secret Key',
    'response': recaptcha_token,
    'remoteip': request.remote_addr
}
resp = requests.post(verify_url, data=data)
result = resp.json()
if not result.get('success'):
    # 驗證失敗處理
    ...
```

---

## 6. 注意事項
- Secret Key 請勿公開，建議用環境變數管理。
- 若需隱形驗證，可選擇 reCAPTCHA v2 Invisible 或 v3。
- 詳細官方說明：https://developers.google.com/recaptcha/docs/v2

---

如需協助，請聯絡開發人員。