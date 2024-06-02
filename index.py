import psycopg2
import urllib.parse as urlparse
import os
from dotenv import load_dotenv
from urllib.request import urlopen
import json
import pytz
from datetime import datetime
import pandas as pd
from linebot.exceptions import LineBotApiError
from linebot import LineBotApi
from linebot.models import TextSendMessage

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
            print("データベースに接続されました")
        return conn
    except Exception as e:
        print(f"DBエラーが発生しました: {e}")

# 天気アイコンを設定する関数
def get_weather_icon(icon_str):
    if icon_str == "01d" or icon_str == "01n":
        return "☀️"
    elif (
        icon_str == "02d"
        or icon_str == "02n"
        or icon_str == "03d"
        or icon_str == "03n"
        or icon_str == "04d"
        or icon_str == "04n"
    ):
        return "☁️"
    elif (
        icon_str == "09d" or icon_str == "09n" or icon_str == "10d" or icon_str == "10n"
    ):
        return "☂️"
    elif icon_str == "11d" or icon_str == "11n":
        return "⚡️"
    elif icon_str == "13d" or icon_str == "13n":
        return "☃️"
    else:
        return ""

# 文章内容を整形してLineに送信する関数
def send_to_line(user_id, df):
    texts = []
    for i, (today, data) in enumerate(df):
        if i == 0:
            texts.append(f"【{today}】")
            place = ""

            for _, d in data.iterrows():
                if place == "" or place != f"{d['place']}":
                    texts.append(f"{d['place']}")
                texts.append(
                    f"{d['time']}時 {get_weather_icon(d['icon'])} {d['temp']}℃　 降水確率:{d['pop']}%"
                )
                place = f"{d['place']}"

    line_bot = LineBotApi(os.environ.get("LINE_ACCESS_TOKEN"))
        
    try:
        line_bot.multicast(user_id.split(","), TextSendMessage(text="\n".join(texts)))
        print('成功')
    except LineBotApiError as e:
        print('send_to_line関数内でエラーが発生しました。')
        print('Error occurred: {}'.format(e))

# ファイル実行時の関数
def main():
    # envファイルから環境変数を読み込む
    load_dotenv()
    own_api_key = os.environ.get("OWM_API_KEY")

    # DB接続
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, prefecture, city FROM users")

    for row in cursor:
        user_id = row[0]
        prefecture_id = row[1]
        city_id = row[2]
        if user_id:
            url_weather = "http://api.openweathermap.org/data/2.5/forecast"
            url_city_name = "https://api.openweathermap.org/data/2.5/weather?"
            # cityがあるとき
            if city_id is not None:
                res = urlopen(f"{url_weather}?id={city_id}&appid={own_api_key}&lang=ja&units=metric").read()
                place_data = urlopen(f"{url_city_name}id={city_id}&appid={own_api_key}&lang=ja").read()
            elif prefecture_id is not None:
                res = urlopen(f"{url_weather}?id={prefecture_id}&appid={own_api_key}&lang=ja&units=metric").read()
                place_data = urlopen(f"{url_city_name}id={prefecture_id}&appid={own_api_key}&lang=ja").read()
            else:
                continue

            res_json = json.loads(res)
            place_json = json.loads(place_data)
            city_name = place_json['name']
            
            arr_rj = []
            for rj in res_json["list"]:
                conv_rj = {}
                timezone = pytz.timezone("Asia/Tokyo")
                timestamp = datetime.fromtimestamp(rj["dt"], tz=timezone)
                weekday_japanese = ["月", "火", "水", "木", "金", "土", "日"][timestamp.weekday()]
                conv_rj["date"] = timestamp.strftime("%m月%d日 {}曜日".format(weekday_japanese))
                conv_rj["place"] = f"★{city_name}の天気"
                conv_rj["time"] = timestamp.strftime("%H")
                conv_rj["description"] = rj["weather"][0]["description"]
                conv_rj["icon"] = rj["weather"][0]["icon"]
                conv_rj["temp"] = round(rj["main"]["temp"])
                conv_rj["pop"] = int(rj['pop'] * 100)
                arr_rj.append(conv_rj)
            
            try:
                send_to_line(user_id, pd.DataFrame(arr_rj).groupby("date"))
                print('正常にメッセージを送信できました！')
            except LineBotApiError as e:
                print('main関数内でエラーが発生しました。')
                print('Error occurred: {}'.format(e))

    # 接続を閉じる
    cursor.close()
    connection.close()
    print("データベースを切断しました")

main()
