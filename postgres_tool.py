import click
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

@click.command()
@click.argument('sql', required=False, default='select 1')
def run_sql(sql):
    """執行傳入的 SQL 指令，並顯示結果。"""
    # 取得資料庫連線資訊
    db_host = config.DB_HOST
    db_port = config.DB_PORT or '5432'
    db_password = config.DB_PASSWORD
    db_user = 'postgres'  # 可根據實際情況調整
    db_name = 'postgres'  # 可根據實際情況調整

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
