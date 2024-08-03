# ライブラリ
import os
import random
import string
import gspread
import json
from google.oauth2 import service_account
from argparse import ArgumentParser
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import InvalidSignatureError
from linebot.exceptions import LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# 別ファイル呼び出し
import dbConnect

# 環境変数呼び出し
app = Flask(__name__)
load_dotenv()
LINE_ACCESS_TOKEN = LineBotApi(os.getenv("LINE_ACCESS_TOKEN"))
Handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))



# 環境変数から認証情報を取得
credentials_info = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
# Google Sheets APIにアクセスするためのクレデンシャルを作成
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
# gspreadでGoogle Sheetsにアクセス
gc = gspread.authorize(credentials)
# スプレッドシートを開く
sheet_name = 'DailySmartLog'
wks = gc.open(sheet_name).sheet1
# セルにデータを更新
wks.update_cell(1, 1, 'Pythonから入力')



# lineMessagingAPIからのアクセスを受付
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        # 署名検証とイベント処理
        Handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'line connect status 200'

# アクセスしたユーザーのLineに返信
@Handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # アクセスユーザーIDの取得
    profile = LINE_ACCESS_TOKEN.get_profile(event.source.user_id)
    userId = profile.user_id
    # 送信されたメッセージが設定済みのメッセージか判定
    setMessage = os.getenv("SET_MESSAGE")
    getMessage = event.message.text
    if getMessage != setMessage: exit()
    textMessage = ""
    # トークンを特例として許可
    if (event.reply_token == '00000000000000000000000000000000' or
            event.reply_token == 'ffffffffffffffffffffffffffffffff'):
        app.logger.info('Verify Event Received')
        return
    # DB接続
    connection = dbConnect.db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (userId,))

    # アクセスユーザーが初回登録か判定しワンタイムキーの発行とDBへの追加
    registCheckFlag = cursor.fetchone()
    if registCheckFlag is None:
        oneTimeKey = get_random_string(12)
        try:
            cursor.execute("INSERT INTO users (user_id, otk) VALUES (%s, %s)", (userId, oneTimeKey))
            connection.commit()
        except Exception as e:
            print(f"Error inserting {userId}: {e}")
        textMessage = f"ワンタイム認証キー：{oneTimeKey}"
    else:
        textMessage = "登録済みユーザーです"
    
    # DB接続を閉じる
    cursor.close()
    connection.close()
    print("DB closed")

    # ユーザーにプッシュ通知
    try:
        LINE_ACCESS_TOKEN.multicast([userId], TextSendMessage(text=textMessage))
    except LineBotApiError as e:
        print(f"Error: {e}")

# ランダムなワンタイム認証キーを生成
def get_random_string(num):
    LETTERS = string.ascii_letters
    random_letters = random.choices(LETTERS, k=num)
    random_string = ''.join(random_letters)
    return random_string

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)