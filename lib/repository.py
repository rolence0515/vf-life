import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from lib.user_repository import get_db_conn

class BatchAccountLogRepository:
    def __init__(self):
        self.conn = get_db_conn()
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

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
