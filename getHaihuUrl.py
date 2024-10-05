import bs4
import csv # モジュール"CSV"の呼び出し
# import glob
import pathlib
import re

# 牌譜リストのHTMLはnodocchi.moeで抽出した結果を検証モードのタグを選択して右クリックでコピー取得
# 該当フォルダ内のHTMLファイルから牌譜URLを抽出する
files = pathlib.Path('2021').glob('*.html')

def is_tenhou_url(url):
    if not isinstance(url, str):
        return False
    pattern = r'^https?://(?:www\.)?tenhou\.net/.*'
    return bool(re.match(pattern, url))

for file in files:
    # print(file)
    # スクレイピング対象のhtmlファイルからsoupを作成
    soup = bs4.BeautifulSoup(open(file,'r',encoding="utf-8_sig"), 'html.parser')

    links = soup.find_all('a') # 全てのaタグ要素を取得

    csvList = [] # 配列を作成

    for link in links: # aタグのテキストデータを配列に格納
        href = link.get('href')
        if is_tenhou_url(href):
            tmp = href.split('&amp')
            csvList.append(tmp[0])

    # CSVファイルを開く。ファイルがない場合は新規作成
    fileName = file.name
    # fileName = fileName[3:]
    fileName = fileName[:-4]
    with open("output_"+ fileName +"csv", "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(csvList) # 出力
        f.close() # CSVファイルを閉じる
