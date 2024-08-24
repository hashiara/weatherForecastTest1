# ライブラリ
import os
from dotenv import load_dotenv
from urllib.request import urlopen
import json
import datetime
from linebot.exceptions import LineBotApiError
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 別ファイル呼び出し
import dbConnect
from const import BIRTH_MESSAGE, ZODIAC

# 生年月日から星座を特定
def zodiac_check(birth_md):
    zodiac = ZODIAC
    birth_month, birth_day = map(int, birth_md.split('-'))

    for i in range(len(zodiac)):
        if zodiac[i][1] == int(birth_month):
            if zodiac[i][2] <= int(birth_day):
                return zodiac[i][0]
            else:
                return zodiac[i-1][0]

# 文章内容をLineに送信
def send_to_line(line_access_token, user_id, text):
    line_bot = LineBotApi(line_access_token)
        
    try:
        line_bot.multicast(user_id.split(","), TextSendMessage(text))
        print('push to line Code:200')
    except LineBotApiError as e:
        print('push to line:error')
        print('Error occurred: {}'.format(e))

# ファイル実行時の関数
def main():
    # envファイルから環境変数を読み込む
    load_dotenv()
    line_access_token = os.environ.get("LINE_ACCESS_TOKEN")

    # DB接続
    connection = dbConnect.db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, user_name, birth FROM users")

    for row in cursor:
        user_id = row[0]
        user_name = row[1]
        birth = row[2]
        if user_id is not None and birth is not None:
            today = datetime.date.today()
            today_md = today.strftime("%m-%d")
            birth_md = birth.strftime("%m-%d")

            # 誕生日の人へバースデーメッセージ送信
            if today_md == birth_md:
                birth_message = BIRTH_MESSAGE.format(user_name=user_name)
                send_to_line(line_access_token, user_id, birth_message)

            # 星占いメッセージ送信
            formatted_today = today.strftime("%Y/%m/%d")
            url_horoscope = f"http://api.jugemkey.jp/api/horoscope/free/{formatted_today}"
            res = urlopen(url_horoscope).read()
            res_json = json.loads(res)
            
            horoscope_data = res_json.get('horoscope', {})
            today_horoscopes = horoscope_data.get(formatted_today, [])
            zodiac = zodiac_check(birth_md)
            
            for rj in today_horoscopes:
                if isinstance(rj, dict) and 'sign' in rj:
                    if rj['sign'] == zodiac:
                        horoscope_message = f"【今日の星占い】\n{rj['sign']}のあなたの運勢はこちら\n☆ラッキーカラー：{rj['color']}\n☆ラッキーアイテム：{rj['item']}\n\n{rj['content']}"
                        send_to_line(line_access_token, user_id, horoscope_message)

    # 接続を閉じる
    cursor.close()
    connection.close()
    print("データベースを切断しました")

main()
