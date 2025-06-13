import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

class SeriesRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DB_HOST,
            port=getattr(config, 'DB_PORT', 5432),
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def get_all_series(self):
        self.cur.execute('''
            SELECT s.*, COUNT(v.id) AS video_count
            FROM series s
            LEFT JOIN videos v ON v.series_id = s.id
            GROUP BY s.id
            ORDER BY s.id DESC
        ''')
        return self.cur.fetchall()

    def get_series_by_id(self, series_id):
        self.cur.execute('SELECT * FROM series WHERE id = %s', (series_id,))
        return self.cur.fetchone()

    def create_series(self, name, description):
        self.cur.execute('INSERT INTO series (name, description) VALUES (%s, %s) RETURNING id', (name, description))
        self.conn.commit()
        return self.cur.fetchone()['id']

    def update_series(self, series_id, name, description):
        self.cur.execute('UPDATE series SET name = %s, description = %s, updated_at = NOW() WHERE id = %s', (name, description, series_id))
        self.conn.commit()
        return self.cur.rowcount > 0

    def delete_series(self, series_id):
        self.cur.execute('DELETE FROM series WHERE id = %s', (series_id,))
        self.conn.commit()
        return self.cur.rowcount > 0

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
