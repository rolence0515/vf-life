# 初始密碼產生說明

- 新增使用者時，初始密碼會以「Email 字串做 sha256 雜湊後，取前 6 碼」作為密碼。
- 例如：email 為 rolence0515@gmail.com，則密碼為 sha256('rolence0515@gmail.com') 的前 6 碼。
- 產生方式（Python 範例）：

```python
import hashlib
email = 'rolence0515@gmail.com'
password = hashlib.sha256(email.encode()).hexdigest()[:6]
print(password)  # 例如: c7b6ac
```

---

# 資料庫結構說明

## 1. user 使用者表

| 欄位名稱     | 型別         | 說明             |
| ------------ | ------------ | ---------------- |
| id           | SERIAL       | 使用者唯一ID     |
| name         | VARCHAR(255) | 姓名             |
| email        | VARCHAR(255) | 帳號(Email，唯一)|
| password     | VARCHAR(255) | 密碼(加密不可逆) |
| session_token| VARCHAR(255) | 單一登入用的 Session Token |
| created_at   | TIMESTAMP    | 建立日期         |
| updated_at   | TIMESTAMP    | 修改日期         |

```sql
CREATE TABLE "user" (
  id SERIAL PRIMARY KEY, -- 使用者唯一ID
  name VARCHAR(255), -- 姓名
  email VARCHAR(255) UNIQUE NOT NULL, -- 帳號(Email，唯一)
  password VARCHAR(255) NOT NULL, -- 密碼(加密不可逆)
  session_token VARCHAR(255), -- 單一登入用的 Session Token
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 建立日期
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- 修改日期
);
```



---

## 2. user_videos 使用者可觀看影片表

| 欄位名稱     | 型別      | 說明             |
| ------------ | --------- | ---------------- |
| id           | SERIAL    | 唯一ID           |
| user_id      | INTEGER   | 使用者ID         |
| video_id     | INTEGER   | 影片ID           |
| created_at   | TIMESTAMP | 建立日期         |
| updated_at   | TIMESTAMP | 修改日期         |

```sql
CREATE TABLE user_videos (
  id SERIAL PRIMARY KEY, -- 唯一ID
  user_id INTEGER NOT NULL, -- 使用者ID
  video_id INTEGER NOT NULL, -- 影片ID
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 建立日期
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 修改日期
  FOREIGN KEY (user_id) REFERENCES "user"(id),
  FOREIGN KEY (video_id) REFERENCES videos(id)
);
```

---

## 3. series 影片系列表

| 欄位名稱     | 型別         | 說明             |
| ------------ | ------------ | ---------------- |
| id           | SERIAL       | 系列唯一ID       |
| name         | VARCHAR(255) | 系列名稱         |
| description  | TEXT         | 系列說明         |
| created_at   | TIMESTAMP    | 建立日期         |
| updated_at   | TIMESTAMP    | 修改日期         |

```sql
CREATE TABLE series (
  id SERIAL PRIMARY KEY, -- 系列唯一ID
  name VARCHAR(255) NOT NULL, -- 系列名稱
  description TEXT, -- 系列說明
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 建立日期
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- 修改日期
);
```

---

## 4. videos 影片表

| 欄位名稱       | 型別         | 說明                         |
| -------------- | ------------ | ---------------------------- |
| id             | SERIAL       | 影片唯一ID                   |
| series_id      | INTEGER      | 所屬系列ID                   |
| type           | VARCHAR(32)  | 影片來源(vimeo, yt等)        |
| url            | TEXT         | 影片網址                     |
| title          | VARCHAR(255) | 標題                         |
| description    | TEXT         | 說明                         |
| created_at     | TIMESTAMP    | 建立日期                     |
| updated_at     | TIMESTAMP    | 修改日期                     |
| available_at   | TIMESTAMP    | 上架日                       |
| expired_at     | TIMESTAMP    | 下架日(過期不可觀看)         |
| buy_url        | TEXT         | 購買連結                     |
| buy_start_at   | TIMESTAMP    | 開放購買日                   |
| buy_end_at     | TIMESTAMP    | 結束購買日                   |

```sql
CREATE TABLE videos (
  id SERIAL PRIMARY KEY, -- 影片唯一ID
  series_id INTEGER, -- 所屬系列ID
  type VARCHAR(32) NOT NULL, -- 影片來源(vimeo, yt等)
  url TEXT NOT NULL, -- 影片網址
  title VARCHAR(255) NOT NULL, -- 標題
  description TEXT, -- 說明
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 建立日期
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 修改日期
  available_at TIMESTAMP NOT NULL, -- 上架日
  expired_at TIMESTAMP NOT NULL, -- 下架日(過期不可觀看)
  buy_url TEXT, -- 購買連結
  buy_start_at TIMESTAMP, -- 開放購買日
  buy_end_at TIMESTAMP, -- 結束購買日
  FOREIGN KEY (series_id) REFERENCES series(id)
);
```

---

## 5. admin_users 管理員會員關聯表

| 欄位名稱   | 型別    | 說明               |
| ---------- | ------- | ------------------ |
| id         | SERIAL  | 唯一ID             |
| user_id    | INTEGER | 使用者ID (唯一)    |
| created_at | TIMESTAMP | 建立日期         |
| updated_at | TIMESTAMP | 修改日期         |

```sql
CREATE TABLE admin_users (
  id SERIAL PRIMARY KEY, -- 唯一ID
  user_id INTEGER UNIQUE NOT NULL, -- 使用者ID (唯一，1位會員只能有1筆管理員關聯)
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 建立日期
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 修改日期
  FOREIGN KEY (user_id) REFERENCES "user"(id)
);
```
