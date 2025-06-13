import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

from config import config

class BatchAccountLogRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def get_recent_logs(self, limit=20):
        sql = '''
            SELECT 
                id,
                created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Taipei' AS created_at,
                operator_name,
                operator_email,
                backup_checked,
                status,
                fail_reason,
                total_count,
                new_user_count,
                exist_user_count,
                total_videos_count,
                result_filename
            FROM batch_account_log
            ORDER BY created_at DESC
            LIMIT %s
        '''
        self.cur.execute(sql, (limit,))
        return self.cur.fetchall()

    def insert_log(self, operator_name, operator_email, backup_checked, status, fail_reason,
                   total_count, new_user_count, exist_user_count, total_videos_count, result_filename):
        sql = '''
            INSERT INTO batch_account_log (
                created_at, operator_name, operator_email, backup_checked, status, fail_reason,
                total_count, new_user_count, exist_user_count, total_videos_count, result_filename
            ) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        '''
        self.cur.execute(sql, (
            operator_name, operator_email, backup_checked, status, fail_reason,
            total_count, new_user_count, exist_user_count, total_videos_count, result_filename
        ))
        self.conn.commit()
        return self.cur.fetchone()['id']

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
