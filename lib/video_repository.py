
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config
import pytz
from datetime import datetime

class VideoRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )

    def get_all_videos(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT v.id, v.series_id, s.name AS series_name, v.url, v.title,
                       v.created_at, v.updated_at, v.available_at, v.expired_at
                FROM videos v
                LEFT JOIN series s ON v.series_id = s.id
                ORDER BY v.id ASC
            ''')
            videos = cur.fetchall()
            # 格式化日期
            for v in videos:
                for k in ['created_at', 'updated_at', 'available_at', 'expired_at']:
                    if v.get(k):
                        v[k] = v[k].strftime('%Y-%m-%d')
            return videos

    def create_video(self, data):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO videos (series_id, url, title, type, created_at, updated_at, available_at, expired_at)
                VALUES (%s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s, %s)
                RETURNING id
            ''', (
                data.get('series_id'),
                data.get('url'),
                data.get('title'),
                'vimeo',  # type 欄位寫死 vimeo
                data.get('available_at'),
                data.get('expired_at')
            ))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            return new_id

    def update_video(self, video_id, data):
        with self.conn.cursor() as cur:
            cur.execute('''
                UPDATE videos
                SET series_id=%s, url=%s, title=%s, updated_at=CURRENT_DATE,
                    available_at=%s, expired_at=%s
                WHERE id=%s
            ''', (
                data.get('series_id'),
                data.get('url'),
                data.get('title'),
                data.get('available_at'),
                data.get('expired_at'),
                video_id
            ))
            self.conn.commit()
            return cur.rowcount > 0

    def delete_video(self, video_id):
        with self.conn.cursor() as cur:
            cur.execute('DELETE FROM videos WHERE id=%s', (video_id,))
            self.conn.commit()
            return cur.rowcount > 0

    def get_videos_with_status(self, user_email, series_id=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 取得 user_id
            cur.execute('SELECT id FROM "user" WHERE email = %s', (user_email,))
            user = cur.fetchone()
            user_id = user['id'] if user else None
            # 查詢所有影片，若有 series_id 則加上條件
            sql = '''
                SELECT v.id, s.name as series, v.title, v.available_at, v.expired_at, v.url, v.buy_url, uv.id as owned
                FROM videos v
                JOIN series s ON v.series_id = s.id
                LEFT JOIN user_videos uv ON uv.video_id = v.id AND uv.user_id = %s
            '''
            params = [user_id]
            if series_id:
                sql += ' WHERE v.series_id = %s'
                params.append(series_id)
            sql += ' ORDER BY v.available_at ASC'
            cur.execute(sql, tuple(params))
            videos = cur.fetchall()
            result = []
            now = datetime.now(pytz.timezone('Asia/Taipei')).date()
            for v in videos:
                available = v['available_at']
                expired = v['expired_at']
                if isinstance(available, datetime):
                    available = available.date()
                if isinstance(expired, datetime):
                    expired = expired.date()
                if v['owned']:
                    if now < available:
                        status = 'bought_not_started'
                    elif available <= now <= expired:
                        status = 'bought_open'
                    else:
                        status = 'bought_ended'
                else:
                    if now < available:
                        status = 'not_bought_can_buy'
                    elif available <= now <= expired:
                        status = 'not_bought_can_buy'
                    else:
                        status = 'not_bought_expired'
                result.append({
                    'series': v['series'],
                    'title': v['title'],
                    'period': f"{v['available_at'].strftime('%Y/%m/%d')} ~ {v['expired_at'].strftime('%Y/%m/%d')}",
                    'vimeoUrl': v['url'] or 'https://player.vimeo.com/video/123456789',
                    'status': status,
                    'buy_url': v.get('buy_url')
                })
            return result

    def get_all_series(self):
        with self.conn.cursor() as cur:
            cur.execute('SELECT id, name FROM series ORDER BY id ASC')
            return [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]

    def get_next_available_video(self, today):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 查詢距離今天最近的 available_at 日期的影片
            sql = '''
                SELECT title, available_at, expired_at
                FROM videos
                WHERE available_at > %s
                ORDER BY available_at ASC
                LIMIT 1
            '''
            cur.execute(sql, (today,))
            return cur.fetchone()

    def close(self):
        self.conn.close()
