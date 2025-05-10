import os
import click
import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv


@click.command()
@click.argument('env', required=True)
@click.argument('sql', required=False, default='CREATE TABLE \"user\" (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);')
def run_sql(env, sql):
    """執行傳入的 SQL 指令，並顯示結果。支援環境切換。"""

    # 動態載入環境變數
    if not env or env not in ('uat', 'prod', 'dev'):
        print('請輸入執行環境參數 (dev、uat 或 prod)，例如: python postgres_tool.py uat "select 1"')
        return

    # 根據環境參數載入對應的 .env 檔案
    env_file = f'.env.{env}'
    load_dotenv(env_file)
    print(f'已載入環境檔案: {env_file}')
    from config import config

    # 從 config 載入資料庫連線資訊
    db_host = config.DB_HOST
    db_port = config.DB_PORT or '5432'
    db_password = config.DB_PASSWORD
    db_user = config.DB_USER
    db_name = config.DB_NAME

    # Print the loaded environment variables for debugging
    print("Debugging Environment Variables:")
    print(f"DB_HOST: {db_host}")
    print(f"DB_PORT: {db_port}")
    print(f"DB_USER: {db_user}")
    print(f"DB_NAME: {db_name}")
    print(f"DB_PASSWORD: {db_password}")

    # 等待使用者確認後繼續
    user_input = input("請確認上述環境變數內容無誤，正確請輸入 y 繼續，否則請按其他鍵取消：")
    if user_input.lower() != 'y':
        print("操作已取消。")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name
        )
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            if cur.description:  # 有查詢結果
                rows = cur.fetchall()
                click.echo(f"查詢結果共 {len(rows)} 筆：")
                for row in rows:
                    click.echo(row)
            else:  # 非查詢語句
                conn.commit()
                click.echo(f"SQL 執行成功，影響 {cur.rowcount} 筆資料。")
    except Exception as e:
        click.echo(f"執行 SQL 發生錯誤: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    run_sql()
