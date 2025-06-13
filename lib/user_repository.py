import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

class UserRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )

    def create_user(self, name, email, password):
        """
        建立新 user，回傳 user_id
        """
        with self.conn.cursor() as cur:
            cur.execute('INSERT INTO "user" (name, email, password) VALUES (%s, %s, %s) RETURNING id', (name, email, password))
            user_id = cur.fetchone()[0]
            self.conn.commit()
            return user_id

    def add_user_video(self, user_id, video_id):
        """
        新增 user_videos 權限，若已存在則不重複寫入。成功新增回傳 True，否則 False
        """
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1 FROM user_videos WHERE user_id=%s AND video_id=%s', (user_id, video_id))
            if cur.fetchone():
                return False
            cur.execute('INSERT INTO user_videos (user_id, video_id) VALUES (%s, %s)', (user_id, video_id))
            self.conn.commit()
            return True

    def remove_user_video(self, user_id, video_id):
        """
        刪除 user_videos 權限
        """
        with self.conn.cursor() as cur:
            cur.execute('DELETE FROM user_videos WHERE user_id=%s AND video_id=%s', (user_id, video_id))
            self.conn.commit()
    
    def get_admin_count(self):
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM admin_users')
            return cur.fetchone()[0]

    def add_admin(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute('INSERT INTO admin_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING', (user_id,))
            self.conn.commit()

    def remove_admin(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute('DELETE FROM admin_users WHERE user_id = %s', (user_id,))
            self.conn.commit()

    def get_user_by_id(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM "user" WHERE id = %s', (user_id,))
            return cur.fetchone()
        
    def update_session_token(self, user_id, session_token):
        with self.conn.cursor() as cur:
            cur.execute('UPDATE "user" SET session_token = %s, updated_at = NOW() WHERE id = %s', (session_token, user_id))
            self.conn.commit()
            
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

    def get_users_with_pagination(self, q=None, offset=0, limit=20, admin_only=False):
        with self.conn.cursor() as cur:
            where_clauses = []
            params = []
            if q:
                where_clauses.append('(LOWER(u.email) LIKE %s OR LOWER(u.name) LIKE %s)')
                params.extend([f'%{q}%', f'%{q}%'])
            if admin_only:
                where_clauses.append('a.user_id IS NOT NULL')
            where_sql = ''
            if where_clauses:
                where_sql = 'WHERE ' + ' AND '.join(where_clauses)
            # 查詢用戶
            sql = f'''
                SELECT u.id, u.email, u.name, u.created_at, u.updated_at,
                    CASE WHEN a.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_admin
                FROM "user" u
                LEFT JOIN admin_users a ON u.id = a.user_id
                {where_sql}
                ORDER BY u.id
                LIMIT %s OFFSET %s
            '''
            params.extend([limit, offset])
            cur.execute(sql, tuple(params))
            users = [
                {
                    'id': row[0],
                    'email': row[1],
                    'name': row[2],
                    'created_at': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'updated_at': row[4].strftime('%Y-%m-%d') if row[4] else '',
                    'is_admin': row[5]
                }
                for row in cur.fetchall()
            ]
            # 查詢總數
            count_sql = f'''
                SELECT COUNT(*)
                FROM "user" u
                LEFT JOIN admin_users a ON u.id = a.user_id
                {where_sql}
            '''
            cur.execute(count_sql, tuple(params[:-2]))
            total = cur.fetchone()[0]
            return users, total
