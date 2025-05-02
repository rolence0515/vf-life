import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

class VideoRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )

    def get_videos_with_status(self, user_email):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 取得 user_id
            cur.execute('SELECT id FROM "user" WHERE email = %s', (user_email,))
            user = cur.fetchone()
            user_id = user['id'] if user else None
            # 查詢所有影片
            cur.execute('''
                SELECT v.id, s.name as series, v.title, v.available_at, v.expired_at, v.url, uv.id as owned
                FROM videos v
                JOIN series s ON v.series_id = s.id
                LEFT JOIN user_videos uv ON uv.video_id = v.id AND uv.user_id = %s
                ORDER BY v.available_at ASC
            ''', (user_id,))
            videos = cur.fetchall()
            result = []
            for v in videos:
                # 狀態判斷
                today = cur.mogrify('CURRENT_DATE').decode()
                # 這裡直接用 Python 判斷
                from datetime import date
                available = v['available_at']
                expired = v['expired_at']
                import datetime
                now = datetime.datetime.now().date()
                # 修正型別比較問題
                if isinstance(available, datetime.datetime):
                    available = available.date()
                if isinstance(expired, datetime.datetime):
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
                    'status': status
                })
            return result

    def close(self):
        self.conn.close()
