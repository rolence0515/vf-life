import os
import click
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

@click.command()
@click.argument('env', required=False, default='dev')
@click.argument('sql', required=False, default='select 1')
def run_sql(env, sql):
    """執行傳入的 SQL 指令，並顯示結果。支援環境切換。"""
    #===== 1. 檢查與載入環境參數 =====
    if not env or env not in ('uat', 'prod', 'dev'):
        print('請輸入執行環境參數 (dev、uat 或 prod)，例如: python postgres_tool.py uat "select 1"')
        return
    env_file = f'.env.{env}'
    if not os.path.exists(env_file):
        print(f'找不到 {env_file}，請確認檔案存在於當前目錄')
        return
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ[k] = v
            env_vars[k] = v
    print(f'已載入 {env_file}，內容如下：')
    for k, v in env_vars.items():
        print(f'{k}={v}')
    confirm_env = input('請確認上述環境變數內容無誤，正確請輸入 y 繼續，否則請按其他鍵取消：')
    if confirm_env.strip().lower() != 'y':
        print('已取消執行。')
        return
    from config import config

    # 取得資料庫連線資訊
    db_host = config.DB_HOST
    db_port = config.DB_PORT or '5432'
    db_password = config.DB_PASSWORD
    db_user = config.DB_USER
    db_name = config.DB_NAME

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
