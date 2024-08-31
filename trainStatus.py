# ライブラリ
import os
from dotenv import load_dotenv
from urllib.request import urlopen, Request
import json
from datetime import datetime, time
from linebot.exceptions import LineBotApiError
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 別ファイル呼び出し
import dbConnect

# 文章内容をLineに送信
def send_to_line(line_access_token, user_id, rail, formatted_last_updated, src):
    line_bot = LineBotApi(line_access_token)
    text = f"【{rail['railName']}の運行状況】\n{formatted_last_updated}時点の運行状況\n\n{rail['status']}\n{rail['info']}\n\n詳細はこちらで検索\n{src}"
        
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
    cursor.execute("""SELECT users.user_id, train.area_code, train.rail_order, train.last_train_status 
                   FROM users 
                   JOIN train ON users.user_id = train.user_id""")

    rows = cursor.fetchall()
    for row in rows:
        user_id = row[0]
        area_code = str(row[1])
        rail_order = row[2]
        last_train_status = row[3]
        if all(val is not None for val in [user_id, area_code, rail_order]):

            # 路線情報url取得
            url_trainStatus = "https://ntool.online/data/train_all.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
            }
            
            req = Request(url_trainStatus, headers=headers)
            res = urlopen(req).read()
            res_json = json.loads(res)
            
            last_updated = res_json.get('lastUpdated', {})
            data = res_json.get('data', {})
            src = res_json.get('src', {})

            # 取得した最新更新時刻のフォーマット変換
            timestamp_s = last_updated / 1000
            dt = datetime.fromtimestamp(timestamp_s)
            formatted_last_updated = dt.strftime('%Y年%m月%d日 %H時%M分')

            # 時刻比較用
            current_time = datetime.now().time()
            start_time = time(8, 0, 0)
            end_time = time(23, 59, 59)
            
            # 路線情報メッセージ送信
            for area in data:
                if area == area_code:
                    rails = data[area]
                    rail = rails[rail_order]
                    if len(rails) > 0 and rail:
                        # 現在時刻が0時を過ぎていない
                        # rail['status']がlast_train_statusと異なる
                        # last_train_statusがNone
                        if start_time <= current_time <= end_time and rail['status'] != last_train_status:
                            send_to_line(line_access_token, user_id, rail, formatted_last_updated, src)
                            try:
                                cursor.execute("""UPDATE train 
                                               SET last_train_status = %s
                                               WHERE user_id = %s""", 
                                               (rail['status'], user_id))
                                connection.commit()
                            except Exception as e:
                                print(f"Error updating {user_id}: {e}")
                        elif end_time < current_time:
                            try:
                                cursor.execute("""UPDATE train 
                                               SET last_train_status = Null
                                               WHERE user_id = %s""", 
                                               (user_id,))
                                connection.commit()
                            except Exception as e:
                                print(f"Error updating {user_id}: {e}")
                        else:
                            continue

    # 接続を閉じる
    cursor.close()
    connection.close()
    print("データベースを切断しました")

main()
