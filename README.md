# vf-life

```bash
gcloud app deploy app.yaml --version=uat --no-promote --quiet
```


```bash
ALTER TABLE videos
ALTER COLUMN expired_at DROP NOT NULL;
```


-- 我要將所有series中的description的欄位值改為:
-- '聯票的購買資料會由售票系統於活動開始前 8 天統一匯入本系統。<br/>
--                   如果你已購買聯票，卻在這裡看到「未購買」的狀態，請不用擔心，等候匯入作業完成後即可正常觀看回放。如有疑問請
--                   <a href="https://reurl.cc/aeXj9Y" target="_blank" rel="noopener">聯絡商城客服協助</a>。'
UPDATE
  "public"."series"
SET
  "description" = '聯票的購買資料會由售票系統於活動開始前 8 天統一匯入本系統。<br/>
                  如果你已購買聯票，卻在這裡看到「未購買」的狀態，請不用擔心，等候匯入作業完成後即可正常觀看回放。如有疑問請
                  <a href="https://reurl.cc/aeXj9Y" target="_blank" rel="noopener">聯絡商城客服協助</a>。';