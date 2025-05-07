# Cloud SQL UAT 與 PROD 環境建立指令與說明

本文件說明如何建立 UAT（測試）與 PROD（正式）兩個不同規格的 Cloud SQL for PostgreSQL 16 實例，並說明其適用情境。

---

## UAT（測試環境）

```bash
gcloud sql instances create vf-life-uat-db \
  --database-version=POSTGRES_16 \
  --tier=db-perf-optimized-N-2 \
  --region=asia-east2 \
  --project=ardent-strength-459016-s3 \
  --root-password='u7p3w9d2k6r1a8b0'
```

- **說明**：
  - 適合開發、測試、UAT 使用。
  - `db-perf-optimized-N-2` 為 2GB RAM，屬於最低規格，僅建議小流量或功能驗證用途。
  - 若需大量測試或多用戶同時連線，建議升級規格。

---

## PROD（正式環境）

```bash
gcloud sql instances create vf-life-prod-db \
  --database-version=POSTGRES_16 \
  --tier=db-perf-optimized-N-4 \
  --region=asia-east2 \
  --project=ardent-strength-459016-s3 \
  --root-password='u7p3w9d2k6r1a8b0'
```

- **說明**：
  - 適合正式上線、穩定服務使用。
  - `db-perf-optimized-N-4` 為 4GB RAM，建議作為生產環境的最低規格。
  - 可支援較多同時連線（建議 20～50 條），如有更高流量需求可再升級。

---

> ⚠️ 兩個環境請分開建立，避免測試資料影響正式資料。密碼建議依實際安全政策定期更換。
>  
> 更多機型與費用資訊請參考 [Cloud SQL 官方文件](https://cloud.google.com/sql/docs/postgres/create-instance#machine-types)。
