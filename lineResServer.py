# ライブラリ
import os
from argparse import ArgumentParser
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
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

# アクセスしたユーザーが初回登録か登録済みか判定しLineに返信
@Handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 受け取ったメッセージをそのまま返す
    LINE_ACCESS_TOKEN.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

if __name__ == "__main__":
    app.run()




# # DB接続
# connection = dbConnect.db_connect()
# cursor = connection.cursor()
# cursor.execute("SELECT user_id FROM users")

# for row in cursor:
#     user_id = row[0]
#     prefecture_id = row[1]
#     city_id = row[2]
#     if user_id:
#         try:
#             send_to_line(user_id, pd.DataFrame(arr_rj).groupby("date"))
#             print('正常にメッセージを送信できました！')
#         except LineBotApiError as e:
#             print('main関数内でエラーが発生しました。')
#             print('Error occurred: {}'.format(e))

# # 接続を閉じる
# cursor.close()
# connection.close()
# print("DB Closed")