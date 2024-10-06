import requests
import csv
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# セッションの設定
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# ユーザーエージェントの設定
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# url一覧を取得しファイルを生成する
with open("./output_luckyj.csv") as f:
    for row in csv.reader(f):
        for url in row:
            # url一覧をもとにアクセスしてソースを取得する
            logUrl = 'https://tenhou.net/0/log/?' + url[26:-5]
            try:
                response = session.get(logUrl, headers=headers, allow_redirects=True)
                response.raise_for_status()
                content = response.text
                
                # 取得したソースをフォルダに保存する
                path = './luckyj/' + url[26:-5] + '.txt'
                with open(path, 'w', encoding='utf-8') as txt:
                    txt.write(content)
            except requests.exceptions.RequestException as e:
                print(f"取得失敗: {logUrl}, エラー: {e}")
