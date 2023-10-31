import json
import os
import pandas as pd
from dotenv import load_dotenv
from urllib.request import urlopen
from datetime import datetime
from pytz import timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
import pytz

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


def send_to_line(df):
    texts = []
    count = 1
    for k, v in df:
        if count == 1:
            texts.append(f"【{k}】")
            place = ""

            for _, d in v.iterrows():
                if place == "" or place != f"{d['place']}":
                    texts.append(f"{d['place']}")
                texts.append(
                    f"{d['time']}時 {get_weather_icon(d['icon'])} {d['temp']}℃　 [{d['rain']}mm/3h]"
                )
                place = f"{d['place']}"

            texts.append("")
            count += 1

    line_bot = LineBotApi(os.environ.get("LINE_ACCESS_TOKEN"))
        
    try:
        line_bot.multicast(os.environ.get("LINE_USER_ID").split(","), TextSendMessage(text="\n".join(texts)))
        print('成功')
    except LineBotApiError as e:
        print('send_to_line関数内でエラーが発生しました。')
        print('Error occurred: {}'.format(e))


def main():
    load_dotenv()  # .env ファイルから環境変数を読み込む
    url = "http://api.openweathermap.org/data/2.5/forecast"
    ids = os.environ.get("OWM_PLACE_ID").split(",")
    api_key = os.environ.get("OWM_API_KEY")

    arr_rj = []

    for count, id in enumerate(ids, start=1):
        res = urlopen(f"{url}?id={id}&appid={api_key}&lang=ja&units=metric").read()
        res_json = json.loads(res)

        if count == 1:
            owm_place = "■大阪市の天気"
        elif count == 2:
            owm_place = "■小浜市の天気"
        elif count == 3:
            owm_place = "■浜松市の天気"

        for rj in res_json["list"]:
            conv_rj = {}
            timezone = pytz.timezone("Asia/Tokyo")
            timestamp = datetime.fromtimestamp(rj["dt"], tz=timezone)
            weekday_japanese = ["月", "火", "水", "木", "金", "土", "日"][timestamp.weekday()]
            conv_rj["date"] = timestamp.strftime("%m月%d日 {}曜日".format(weekday_japanese))
            conv_rj["place"] = owm_place
            conv_rj["time"] = timestamp.strftime("%H")
            conv_rj["description"] = rj["weather"][0]["description"]
            conv_rj["icon"] = rj["weather"][0]["icon"]
            conv_rj["temp"] = round(rj["main"]["temp"])
            conv_rj["rain"] = round(rj["rain"]["3h"], 1) if "rain" in rj else 0
            arr_rj.append(conv_rj)

    try:
        send_to_line(pd.DataFrame(arr_rj).groupby("date"))
        print('正常にメッセージを送信できました！')
    except LineBotApiError as e:
        print('main関数内でエラーが発生しました。')
        print('Error occurred: {}'.format(e))

main()