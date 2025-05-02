當然可以～Cindy 幫你重新整理這份 README，變得更完整、更清楚、適合團隊使用開發與部署 PostgreSQL on Cloud SQL 的標準流程 👇

---

# 📘 Cloud SQL (PostgreSQL) 使用與連線說明

本文件說明如何：

* 建立 Cloud SQL (PostgreSQL)
* 建立程式用資料庫
* 從本機、Cloud Run、App Engine 正確連線
* 設定必要權限與 Cloud SQL 掛載方式
* 理解本機與無伺服器環境連線差異

---

## 🛠️ 1. 建立 Cloud SQL 實例

### ✅ 建立 PostgreSQL 14 實例（建議版本）

```bash
gcloud sql instances create your-db-instance-name \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=asia-east2 \
  --project=your-project-id \
  --root-password='YourStrongPassword123!'
```

> ⚠️ 注意：**POSTGRES\_16 為 ENTERPRISE\_PLUS 類型，無法使用 f1-micro，費用高，建議測試階段使用 POSTGRES\_14。**

---

### ✅ 建立程式使用的資料庫

```bash
gcloud sql databases create your_app_db \
  --instance=your-db-instance-name \
  --project=your-project-id
```

---

## 👮 2. 設定 IAM 權限：讓 Cloud Run / App Engine 可以連線資料庫

### 指定服務帳號加入 Cloud SQL 權限：

```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:your-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

---

## 💻 3. 本機連線（透過「公開 IP」）

### 步驟一：查詢實例的「公開 IP」

GCP Console → SQL → 實例 →「連線」→ 公開 IP

---

### 步驟二：將你的本機 IP 加入授權名單（白名單）

```bash
curl ifconfig.me  # 取得你的 IP

gcloud sql instances patch your-db-instance-name \
  --project=your-project-id \
  --authorized-networks=你的本機IP/32
```

---

### 步驟三：使用 PostgreSQL 客戶端連線

```bash
psql -h <實例公開IP> -U postgres -d your_app_db -p 5432
```

### 或用 Python 程式連線：

```python
import psycopg2

conn = psycopg2.connect(
    host='34.xx.xx.xx',
    port='5432',
    user='postgres',
    password='YourStrongPassword123!',
    dbname='your_app_db'
)
```

---

## ☁️ 4. Cloud Run 連線（使用 Unix Socket）

### 步驟一：**部署時綁定 Cloud SQL 實例**

```bash
gcloud run deploy your-service-name \
  --image=gcr.io/your-project-id/your-image \
  --add-cloudsql-instances=your-project-id:asia-east2:your-db-instance-name \
  --service-account=your-service-account@your-project-id.iam.gserviceaccount.com \
  --region=asia-east2 \
  --set-env-vars=DB_HOST=/cloudsql/your-project-id:asia-east2:your-db-instance-name,DB_USER=postgres,DB_NAME=your_app_db,DB_PASSWORD=YourStrongPassword123!
```

---

### 步驟二：Python 程式碼中連線設定

```python
import psycopg2

conn = psycopg2.connect(
    host='/cloudsql/your-project-id:asia-east2:your-db-instance-name',
    user='postgres',
    password='YourStrongPassword123!',
    dbname='your_app_db'
)
```

> ✅ 此方式不需開啟 Cloud SQL 公開 IP，也不需設定防火牆白名單，更安全。

---

## 🌐 5. App Engine 連線 Cloud SQL（Standard）

### `app.yaml` 設定：

```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT app:app

env_variables:
  DB_HOST: /cloudsql/your-project-id:asia-east2:your-db-instance-name
  DB_PORT: 5432
  DB_USER: postgres
  DB_NAME: your_app_db
  DB_PASSWORD: "YourStrongPassword123!"

beta_settings:
  cloud_sql_instances: your-project-id:asia-east2:your-db-instance-name
```

---

## ⚖️ 6. 本機 vs 無伺服器環境差異

| 項目       | 本機開發             | Cloud Run / App Engine 無伺服器 |
| -------- | ---------------- | --------------------------- |
| 連線方式     | 公開 IP + 密碼       | Unix Socket + 授權帳號          |
| 是否需設定白名單 | ✅ 是              | ❌ 否                         |
| 是否需公開 IP | ✅ 是              | ❌ 否                         |
| 安全性      | 低（開放外部 IP）       | 高（僅限 GCP 內部連線）              |
| 是否支援密碼連線 | ✅ 支援             | ✅ 支援                        |
| 是否支援自動掛載 | ❌（手動建 socket 路徑） | ✅ Cloud SQL 自動 mount        |

---

## 🔗 參考資源

* [Cloud SQL 官方文件](https://cloud.google.com/sql/docs/postgres)
* [Cloud Run 連線教學](https://cloud.google.com/sql/docs/postgres/connect-run)
* [App Engine 連線教學](https://cloud.google.com/sql/docs/postgres/connect-app-engine)
* [Cloud SQL 權限設定](https://cloud.google.com/sql/docs/postgres/roles)

---

需要我幫你輸出成 Markdown 檔？或者幫你改成繁體中文版本的 README.md 也沒問題 😄
要幫你加上 `Cloud SQL Proxy` 本機開發方式也可以喔～要嗎？
