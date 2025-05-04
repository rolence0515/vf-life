import click
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config
import csv
import hashlib
import time
import os

# 產生預設密碼（sha256(email)取前6碼）
def gen_default_pw(email):
    return hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]

@click.command()
@click.argument('csv_path', required=True)
def user_buy_serial_tool(csv_path):
    """
    批次匯入會員購買影片系列(csv)，自動建立/查詢會員、開通會員可觀看影片權限。
    輸出結果csv，檔名加timestamp避免覆蓋。
    """
    # 取得資料庫連線資訊
    db_host = config.DB_HOST
    db_port = config.DB_PORT or '5432'
    db_password = config.DB_PASSWORD
    db_user = config.DB_USER
    db_name = config.DB_NAME

    conn = None
    result_rows = []
    timestamp = int(time.time())
    output_csv = f'user_buy_serial_result_{timestamp}.csv'

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name
        )
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 讀取csv
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    email = row['email'].strip()
                    serial1 = int(row.get('serial1', 0))
                    serial2 = int(row.get('serial2', 0))
                    print(f'處理: {email}, serial1={serial1}, serial2={serial2}')

                    # 1. 檢查/建立 user
                    cur.execute("SELECT id FROM \"user\" WHERE email=%s", (email,))
                    user_row = cur.fetchone()
                    if user_row:
                        user_id = user_row['id']
                        new_user = 0
                        default_pw = ''
                        print(f'已存在會員: {email}, user_id={user_id}')
                    else:
                        pw = gen_default_pw(email)
                        cur.execute("INSERT INTO \"user\" (email, password) VALUES (%s, %s) RETURNING id", (email, pw))
                        user_id = cur.fetchone()['id']
                        conn.commit()
                        new_user = 1
                        default_pw = pw
                        print(f'新增會員: {email}, user_id={user_id}, 預設密碼={pw}')

                    # 2. 查詢購買系列對應影片
                    video_ids = set()
                    if serial1 == 1:
                        cur.execute("SELECT id FROM videos WHERE series_id=1")
                        vids = [v['id'] for v in cur.fetchall()]
                        video_ids.update(vids)
                        print(f'  serial1=1, 需開通影片: {vids}')
                    if serial2 == 1:
                        cur.execute("SELECT id FROM videos WHERE series_id=2")
                        vids = [v['id'] for v in cur.fetchall()]
                        video_ids.update(vids)
                        print(f'  serial2=1, 需開通影片: {vids}')

                    # 3. 寫入 user_videos，避免重複
                    add_count = 0
                    for vid in video_ids:
                        cur.execute("SELECT 1 FROM user_videos WHERE user_id=%s AND video_id=%s", (user_id, vid))
                        if not cur.fetchone():
                            cur.execute("INSERT INTO user_videos (user_id, video_id) VALUES (%s, %s)", (user_id, vid))
                            add_count += 1
                            print(f'    新增 user_videos: user_id={user_id}, video_id={vid}')
                        else:
                            print(f'    已存在 user_videos: user_id={user_id}, video_id={vid}')
                    conn.commit()

                    # 4. 統計結果
                    result_rows.append({
                        'email': email,
                        'user_id': user_id,
                        'new_user': new_user,
                        'default_pw': default_pw,
                        'videos_count': add_count
                    })

        # 5. 輸出結果csv
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['email', 'user_id', 'new_user', 'default_pw', 'videos_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in result_rows:
                writer.writerow(r)
        print(f'處理完成，結果已輸出: {output_csv}')

    except Exception as e:
        print(f'發生錯誤: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    user_buy_serial_tool()
