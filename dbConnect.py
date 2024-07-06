import psycopg2
import urllib.parse as urlparse
import os

# データベースに接続する関数
def db_connect():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    url = urlparse.urlparse(DATABASE_URL)

    # 接続情報を取得
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    # データベースへの接続
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        if conn:
            print("DBaccess status 200")
            return conn
    except Exception as e:
        print(f"DBaccess status error: {e}")