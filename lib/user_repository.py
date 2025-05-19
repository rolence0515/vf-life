import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

class UserRepository:
    def update_session_token(self, user_id, session_token):
        with self.conn.cursor() as cur:
            cur.execute('UPDATE "user" SET session_token = %s, updated_at = NOW() WHERE id = %s', (session_token, user_id))
            self.conn.commit()
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )

    def get_user_by_email(self, email):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM "user" WHERE email = %s', (email,))
            return cur.fetchone()

    def update_password(self, user_id, new_password):
        with self.conn.cursor() as cur:
            cur.execute('UPDATE "user" SET password = %s, updated_at = NOW() WHERE id = %s', (new_password, user_id))
            self.conn.commit()
            return cur.rowcount

    def is_admin_user(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM admin_users WHERE user_id = %s', (user_id,))
            return cur.fetchone() is not None

    def close(self):
        self.conn.close()
