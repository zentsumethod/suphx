# import glob
import pathlib
import csv
import os
import numpy as np
# mahjongライブラリ
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter

# 自作関数
from mj_function import convertPai, getDoraStr

# 変数
targetFolder = "luckyj" # 対象フォルダ
# targetFolder = "mjlog" # 対象フォルダ
targetPlayerName = "%E2%93%9D%4C%75%63%6B%79%4A" # 対象プレーヤの名前
# targetPlayerName = "%E2%93%9D%53%75%70%68%78" # suphx

# 該当フォルダ内のHTMLファイルから牌譜URLを抽出する
files = pathlib.Path(targetFolder).glob('*.txt')
listFiles = list(files)
# 解析時間短縮のため、対象ファイルを絞る
# listFiles = listFiles[:1]
# 結果を格納する配列
results = []

for index in range(len(listFiles)):
    with open(listFiles[index]) as f:
        s = f.read()
        id = str(listFiles[index])[7:-4]

        # if id != "2020121810gm-0029-0000-30b10d97":  # バグ改修用
        #     continue

        # mjlogのタグを削除
        s = s[20:-12]
        # タグで文字列を分割
        s = s.split("/><")
        # print(s)
        game = {
            "name": "TAIKYOKU",
            "id": id,
            "type": 0,
            "oya": 0,
            "kyokus": [],
            "target": [],
            "targetPlayerNum": 99,
            "url": "https://tenhou.net/5/?log=" + id,
        }
        for tag in s:
            attrs = tag.split(" ")
            if tag.startswith('SHUFFLE'):
                # print('SHUFFLE')
                continue
            elif tag.startswith('GO'):
                # print('GO')
                for attr in attrs:
                    attrArr = attr.split("=")
                    if attrArr[0] == "type":
                        game['type'] = attrArr[1][1:-1]
                continue
            elif tag.startswith('UN'):
                # print('UN')
                for i in range(len(attrs)):
                    attrArr = attrs[i].split("=")
                    if attrArr[0].startswith('n'):
                        playerName = attrArr[1][1:-1]
                        # 対象プレーヤの座順を把握
                        if playerName == targetPlayerName:
                            game['targetPlayerNum'] = int(attrArr[0][1])
                            game['url'] = "https://tenhou.net/5/?log=" + id + "&tw=" + str(i-1)
                continue
            elif tag.startswith('TAIKYOKU'):
                # print('TAIKYOKU')
                continue
            elif tag.startswith('INIT'):
                # print('INIT')

                # 局単位のオブジェクトを作成
                kyoku = {
                    "ts": 0,
                    "tj": 0,
                    "actionAll": [],
                    "kawaAll": [],
                    "kawas": [[], [], [], []],
                    "tsumos": [[], [], [], []],
                    "haipais": [[], [], [], []],
                    "lastTehais": [[], [], [], []],
                    "dahaiCounts": [0, 0, 0, 0],
                    "flgNaki": [0, 0, 0, 0],
                    "flgReach": [0, 0, 0, 0],
                    "flgCheckEnd": [0, 0, 0, 0],
                    "targetNum": 0,
                    "flgAllLastAssist": False,
                    "info": {
                        "targetPlayerNum": game['targetPlayerNum'],
                        "kyokuNum": -1,
                        "initScores": [],
                        "endScores": [],
                        "tenType": -1,
                        "ten": -1,
                        "oya": -1,
                        "reachNum": -1,
                        "nakiNum": -1,
                        "yaku": [],
                        "who": -1,
                        "fromWho": -1,
                    },
                    "doubleRonInfo": {
                        "targetPlayerNum": game['targetPlayerNum'],
                        "kyokuNum": -1,
                        "initScores": [],
                        "endScores": [],
                        "tenType": -1,
                        "ten": -1,
                        "oya": -1,
                        "reachNum": -1,
                        "nakiNum": -1,
                        "yaku": [],
                        "who": -1,
                        "fromWho": -1,
                    },
                }
                for attr in attrs:
                    attrArr = attr.split("=")
                    if attrArr[0] == "seed":
                        # 内容を配列にし数値に変換
                        kyoku['seed'] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['info']['kyokuNum'] = kyoku['seed'][0]
                    elif attrArr[0] == "ten":
                        kyoku['ten'] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['info']['initScores'] = kyoku['ten']
                    elif attrArr[0] == "oya":
                        kyoku['info']['oya'] = int(attrArr[1][1:-1])
                    elif attrArr[0] == "hai0":
                        kyoku['haipais'][0] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['lastTehais'][0] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                    elif attrArr[0] == "hai1":
                        kyoku['haipais'][1] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['lastTehais'][1] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                    elif attrArr[0] == "hai2":
                        kyoku['haipais'][2] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['lastTehais'][2] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                    elif attrArr[0] == "hai3":
                        kyoku['haipais'][3] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        kyoku['lastTehais'][3] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                # ダブロン対応
                kyoku['doubleRonInfo'] = kyoku['info'].copy() # 値渡しでコピー
                # 局単位のオブジェクトをkyokusに追加する
                game['kyokus'].append(kyoku)
                continue
            elif tag.startswith('DORA'):
                # print('DORA')
                continue
            elif tag.startswith('REACH'):
                # step="2"のみtjとしてカウントする
                if attrs[2] != 'step="1"':
                    # print(attrs[2])
                    game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": int(attrs[1][5:-1]), "type": "reach"})
                continue
            elif tag.startswith('AGARI'):
                # print('AGARI')

                # 1回目のアガリの場合
                info = game['kyokus'][len(game['kyokus'])-1]['info']
                # ダブロンの2回目のアガリの場合
                if info['tenType'] != -1:
                    info = game['kyokus'][len(game['kyokus'])-1]['doubleRonInfo']

                for attr in attrs:
                    attrArr = attr.split("=")
                    if attrArr[0] == "sc":
                        # 局終了時の持ち点配列
                        # scは「対局者0の持ち点 / 100、収支 / 100 〜 対局者3の持ち点 / 100、収支 / 100」の8項なので、点数移動後の値を計算して4項にする
                        scScores = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        info['endScores'] = [scScores[i] + scScores[i+1] for i in range(0, len(scScores), 2)]
                        # 収支情報を持った配列
                        scoresGap = (np.array(info['endScores']) -  np.array(info['initScores'])).tolist()
                        # 対象プレーヤの収支
                        info['ten'] = scoresGap[game['targetPlayerNum']]*100
                    elif attrArr[0] == "yaku":
                        info['yaku'] = ','.join(map(str, map(int, attrArr[1][1:-1].split(','))))
                    elif attrArr[0] == "who":
                        info['who'] = int(attrArr[1][1:-1])
                        # 和了
                        if info['who'] == game['targetPlayerNum']:
                            info['tenType'] = 1
                    elif attrArr[0] == "fromWho":
                        info['fromWho'] = int(attrArr[1][1:-1])
                        if info['fromWho'] == game['targetPlayerNum']:
                            # ツモ和了
                            if info['who'] == info['fromWho']:
                                info['tenType'] = 1
                            
                            # 放銃
                            else:
                                info['tenType'] = 2
                        else:
                            # 横移動
                            if info['who'] != game['targetPlayerNum']:
                                info['tenType'] = 0
                continue
            # 流局
            elif tag.startswith('RYUUKYOKU'):
                # print('RYUUKYOKU')
                info = game['kyokus'][len(game['kyokus'])-1]['info']
                for attr in attrs:
                    attrArr = attr.split("=")
                    if attrArr[0] == "sc":
                        info['tenType'] = 3
                        # scは「対局者0の持ち点 / 100、収支 / 100 〜 対局者3の持ち点 / 100、収支 / 100」の8項なので、点数移動後の値を計算して4項にする
                        scScores = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                        info['endScores'] = [scScores[i] + scScores[i+1] for i in range(0, len(scScores), 2)]
                        # 収支情報を持った配列
                        scoresGap = (np.array(info['endScores']) -  np.array(info['initScores'])).tolist()
                        # 対象プレーヤの収支
                        info['ten'] = scoresGap[game['targetPlayerNum']]*100
                    elif attrArr[0] == "type" and len(attrArr[1][1:-1]) > 0:
                        # nm=流しマンガン,yao9=九種九牌,kaze4=四風連打,reach4=四家立直,ron3=三家和了,kan4=四槓散了
                        info['tenType'] = 4
                        info['ten'] = 0
                continue
            # 回線切れ
            elif tag.startswith('BYE'):
                # print('BYE')
                # <BYE>はtjとしてカウントされない
                # if len(game['kyokus']) > 0: # INIT前に回線切れが発生することがあるため
                # print(game['url'])
                # print("局確認："+str(game['kyokus'][len(game['kyokus'])-1]['seed'][0]))
                continue
            # ツモ牌
            elif tag.startswith('T'):
                # print('T')
                game['kyokus'][len(game['kyokus'])-1]['tsumos'][0].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 0, "type": "tsumo", "pai": int(tag[1:])})
                continue
            elif tag.startswith('U'):
                # print('U')
                game['kyokus'][len(game['kyokus'])-1]['tsumos'][1].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 1, "type": "tsumo", "pai": int(tag[1:])})
                continue
            elif tag.startswith('V'):
                # print('V')
                game['kyokus'][len(game['kyokus'])-1]['tsumos'][2].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 2, "type": "tsumo", "pai": int(tag[1:])})
                continue
            elif tag.startswith('W'):
                # print('W')
                game['kyokus'][len(game['kyokus'])-1]['tsumos'][3].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 3, "type": "tsumo", "pai": int(tag[1:])})
                continue
            # 打牌
            elif tag.startswith('D'):
                # print('D')
                game['kyokus'][len(game['kyokus'])-1]['kawas'][0].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 0, "type": "dahai", "pai": int(tag[1:])})
                continue
            elif tag.startswith('E'):
                # print('E')
                game['kyokus'][len(game['kyokus'])-1]['kawas'][1].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 1, "type": "dahai", "pai": int(tag[1:])})
                continue
            elif tag.startswith('F'):
                # print('F')
                game['kyokus'][len(game['kyokus'])-1]['kawas'][2].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 2, "type": "dahai", "pai": int(tag[1:])})
                continue
            elif tag.startswith('G'):
                # print('G')
                game['kyokus'][len(game['kyokus'])-1]['kawas'][3].append(int(tag[1:]))
                game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 3, "type": "dahai", "pai": int(tag[1:])})
                continue
            # 鳴き
            elif tag.startswith('N'):
                # print('N')
                game['kyokus'][len(game['kyokus'])-1]['kawaAll'].append(tag)
                if attrs[1].startswith('who="0'):
                    game['kyokus'][len(game['kyokus'])-1]['tsumos'][0].append(attrs[2])
                    game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 0, "type": "naki", "pai": attrs[2]})
                elif attrs[1].startswith('who="1'):
                    game['kyokus'][len(game['kyokus'])-1]['tsumos'][1].append(attrs[2])
                    game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 1, "type": "naki", "pai": attrs[2]})
                elif attrs[1].startswith('who="2'):
                    game['kyokus'][len(game['kyokus'])-1]['tsumos'][2].append(attrs[2])
                    game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 2, "type": "naki", "pai": attrs[2]})
                elif attrs[1].startswith('who="3'):
                    game['kyokus'][len(game['kyokus'])-1]['tsumos'][3].append(attrs[2])
                    game['kyokus'][len(game['kyokus'])-1]['actionAll'].append({"playerNum": 3, "type": "naki", "pai": attrs[2]})
                continue

        # print(game)

        # 分析フェーズ
        for i in range(len(game['kyokus'])):
            kyoku = game['kyokus'][i]
            # 局数
            kyokuNum = kyoku['seed'][0]
            # ts=局数として管理する
            kyoku['ts'] = i
            # print('ts:'+str(i))

            # infoを取得
            info = game['kyokus'][i]['info']

            # 打牌、ツモ、鳴きを順番通りに処理する
            for j in range(len(game['kyokus'][i]['actionAll'])):
                action = game['kyokus'][i]['actionAll'][j]
                # tj=巡目として管理する（ツモ、打牌、鳴きのみカウントする）
                if action['type'] == "tsumo" or action['type'] == "dahai" or action['type'] == "naki" or action['type'] == "reach":
                    kyoku['tj'] += 1
                    # print(kyoku['tj'])
                    # playerNumを取得
                    playerNum = action['playerNum']
                    # 調査プレーヤーの調査終了フラグを立っていないことを確認する
                    if kyoku['flgCheckEnd'][game['targetPlayerNum']] == 0:

                        # リーチ
                        if action['type'] == "reach":
                            kyoku['flgReach'][playerNum] = 1

                        # 鳴きがあった場合
                        if action['type'] == "naki":
                            # 該当プレーヤの鳴きフラグを立てる
                            kyoku['flgNaki'][playerNum] += 1

                        # ツモった時
                        elif action['type'] == "tsumo":
                            # ツモ牌を手牌に加える
                            kyoku['lastTehais'][playerNum].append(action['pai'])

                        # 打牌した時
                        elif action['type'] == "dahai":
                            # 手出しチェック（手牌の配列の最後の要素が打牌と同じだった場合ツモ切り）
                            # lastTsumo = kyoku['lastTehais'][playerNum][-1]
                            # if lastTsumo == action['pai']:
                            # print('ツモ切り')

                            # 切った牌を手牌から削除する
                            kyoku['lastTehais'][playerNum].remove(action['pai'])
                            # 打牌数をカウントする
                            kyoku['dahaiCounts'][playerNum] += 1

                            # 調査プレーヤーのオーラス
                            if playerNum == game['targetPlayerNum']:
                                if info['kyokuNum'] == 7:
                                    # 最初に捨てた牌が中張牌だった場合、フラグを立てる
                                    if kyoku['dahaiCounts'][playerNum] == 1 and convertPai(action['pai'])[0] in ['0', '3','4','5','6','7'] and convertPai(action['pai'])[1] != 'z':
                                        kyoku['flgAllLastAssist'] = True
                                        print(game['url']+"&ts="+str(kyoku['ts']))
                                        print(convertPai(action['pai']))
            # CSVに記載するデータとして追加
            results.append([info['targetPlayerNum'], info['kyokuNum'], info['initScores'],info['endScores'], info['tenType'], info['ten'], info['oya'], kyoku['flgReach'][info['targetPlayerNum']], kyoku['flgNaki'][info['targetPlayerNum']], info['yaku'], info['who'], info['fromWho'],game['url']+"&ts="+str(kyoku['ts']), kyoku['flgAllLastAssist']])

            # ダブロン対応
            doubleInfo = game['kyokus'][i]['doubleRonInfo']
            if doubleInfo['tenType'] != -1:
                results.append([doubleInfo['targetPlayerNum'], doubleInfo['kyokuNum'], doubleInfo['initScores'],doubleInfo['endScores'], doubleInfo['tenType'], doubleInfo['ten'], doubleInfo['oya'], kyoku['flgReach'][info['targetPlayerNum']], kyoku['flgNaki'][info['targetPlayerNum']], doubleInfo['yaku'], doubleInfo['who'], doubleInfo['fromWho'],game['url']+"&ts="+str(kyoku['ts']),kyoku['flgAllLastAssist']])

    # 進捗表示
    print(str(index+1)+" / "+str(len(listFiles)))

# 現在のPythonファイル名を取得し、拡張子を.csvに変更
csv_filename = os.path.splitext(os.path.basename(__file__))[0] + '.csv'

with open(csv_filename, 'w', newline="") as f:
    writer = csv.writer(f)
    writer.writerows(results)
