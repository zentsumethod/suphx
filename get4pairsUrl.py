# import glob
import pathlib
import csv
import os
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

# 対象フォルダのファイルを順番に解析する
for index in range(len(listFiles)):
    # ファイルを開く
    with open(listFiles[index]) as f:
        s = f.read()
        # 牌譜IDを取得
        id = str(listFiles[index])[len(targetFolder)+1:-4]

        # if id != "2020121810gm-0029-0000-30b10d97":  # バグ改修用
        #     continue

        # mjlogのタグを削除
        s = s[20:-12]
        # タグで文字列を分割
        s = s.split("/><")

        # 分析用オブジェクト
        game = {
            "id": id,
            "type": 0,
            "oya": 0,
            "kyokus": [],
            "target": [],
            "targetPlayerNum": 99,
            "url": "https://tenhou.net/5/?log=" + id,
        }

        # タグを解析し、分析しやすいようオブジェクトに変換する
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
                            game['targetPlayerNum'] = i - 1
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
                }
                for attr in attrs:
                    attrArr = attr.split("=")
                    if attrArr[0] == "seed":
                        # 内容を配列にし数値に変換
                        kyoku['seed'] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
                    elif attrArr[0] == "ten":
                        kyoku['ten'] = list(map(lambda x: int(x), attrArr[1][1:-1].split(',')))
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
                continue
            elif tag.startswith('RYUUKYOKU'):
                # print('RYUUKYOKU')
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

        # 分析用オブジェクトを解析する
        for i in range(len(game['kyokus'])):
            kyoku = game['kyokus'][i]
            # 局数
            kyokuNum = kyoku['seed'][0]
            # ts=局数として管理する
            kyoku['ts'] = i
            # print('ts:'+str(i))

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

                        # リーチが入った時
                        if action['type'] == "reach":
                            kyoku['flgReach'][playerNum] = 1
                            # 調査終了
                            kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1

                            # 対象プレーヤがリーチした場合
                            # if playerNum == game['targetPlayerNum']:
                            #     # 調査終了
                            #     kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1

                        # 鳴きが入った時
                        if action['type'] == "naki":
                            # 該当プレーヤの鳴きフラグを立てる
                            kyoku['flgNaki'][playerNum] += 1
                            # 調査終了
                            # kyoku['flgCheckEnd'][playerNum] = 1

                            # 鳴いたのが調査プレーヤだった場合
                            if playerNum == game['targetPlayerNum']:
                                # 調査終了
                                kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1
                                # このif文の処理を中断する
                                # 今後の変更対応のため未使用のコードを残しておく
                                break

                                # 鳴きで使った牌を特定し自分の手牌から除去する
                                shouldDeletePai = []
                                mentsuCode = int(action['pai'][3:-1])
                                # 誰から鳴いたか。0: 鳴きなし、1: 下家、2: 対面、3: 上家
                                kui = (mentsuCode & 3)

                                # チーの場合
                                if mentsuCode & (1 << 2):
                                    # print("チー")

                                    # 順子パターン取得
                                    t = (mentsuCode & 0xFC00) >> 10
                                    # どの牌を鳴いたか
                                    nakiPai = t % 3
                                    t = int(t/3)
                                    t = int(t/7)*9+(t % 7)
                                    t *= 4

                                    # 牌種を特定
                                    # nakiPaishu = ['m', 'p', 's'][int(t/7)]
                                    # print(nakiPaishu)

                                    # 鳴いた部分の面子を取得
                                    # print([((mentsuCode & 0x0018) >> 3), ((mentsuCode & 0x0060) >> 5), ((mentsuCode & 0x0180) >> 7)])
                                    # print([t+4*0, t+4*1, t+4*2])
                                    nakiMentsu = [t+4*0+((mentsuCode & 0x0018) >> 3), t+4*1 +
                                                  ((mentsuCode & 0x0060) >> 5), t+4*2+((mentsuCode & 0x0180) >> 7)]
                                    # print(nakiMentsu)

                                    # 手牌に存在していた牌のみ抽出
                                    # shouldDeletePai = list(map(convertPai, nakiMentsu))
                                    shouldDeletePai = nakiMentsu[:]
                                    shouldDeletePai.pop(nakiPai)

                                # ポンの場合
                                elif mentsuCode & (1 << 3):
                                    # print("ポン")

                                    # ポンに関係していない残りの1枚
                                    unused = (mentsuCode & 0x0060) >> 5
                                    # ポンパターン
                                    t = (mentsuCode & 0xFE00) >> 9
                                    r = t % 3
                                    t = int(t/3)
                                    t *= 4
                                    h = [t, t, t]
                                    if unused == 0:
                                        h[0] += 1
                                        h[1] += 2
                                        h[2] += 3
                                    elif unused == 1:
                                        h[0] += 0
                                        h[1] += 2
                                        h[2] += 3
                                    elif unused == 2:
                                        h[0] += 0
                                        h[1] += 1
                                        h[2] += 3
                                    elif unused == 3:
                                        h[0] += 0
                                        h[1] += 1
                                        h[2] += 2

                                    # print(h)
                                    shouldDeletePai = h[:]

                                # 加カンの場合
                                elif mentsuCode & (1 << 4):
                                    # print("加カン")

                                    # 加カンした牌
                                    added = (mentsuCode & 0x0060) >> 5
                                    t = (mentsuCode & 0xFE00) >> 9
                                    r = t % 3
                                    t = int(t/3)
                                    t *= 4
                                    added = t+added

                                    shouldDeletePai.append(added)

                                # 暗カン,大明カンの場合
                                else:
                                    if mentsuCode & 0x0003 == 0:
                                        # print("暗カン")

                                        # 槓子パターンを取得
                                        hai0 = (mentsuCode & 0xFF00) >> 8
                                        t = int(hai0/4)*4
                                        nakiMentsu = [t, t+1, t+2, t+3]
                                        shouldDeletePai = nakiMentsu[:]

                                    else:
                                        # print("大明カン")

                                        # 槓子パターンを取得
                                        hai0 = (mentsuCode & 0xFF00) >> 8
                                        t = int(hai0/4)*4
                                        nakiMentsu = [t, t, t]
                                        # 何番目の牌を鳴いたか
                                        nakiPai = hai0 % 4

                                        if hai0 == 0:
                                            h[0] += 1
                                            h[1] += 2
                                            h[2] += 3
                                        elif hai0 == 1:
                                            h[0] += 0
                                            h[1] += 2
                                            h[2] += 3
                                        elif hai0 == 2:
                                            h[0] += 0
                                            h[1] += 1
                                            h[2] += 3
                                        elif hai0 == 3:
                                            h[0] += 0
                                            h[1] += 1
                                            h[2] += 2
                                        shouldDeletePai = h[:]

                                # print(shouldDeletePai)

                                # さらした牌を手牌から削除する
                                for delPai in shouldDeletePai:
                                    if delPai in kyoku['lastTehais'][playerNum]:
                                        kyoku['lastTehais'][playerNum].remove(delPai)

                        # 牌をツモった時
                        elif action['type'] == "tsumo":
                            # ツモ牌を手牌に加える
                            kyoku['lastTehais'][playerNum].append(action['pai'])

                            # 調査プレーヤーが対象プレーヤだった場合
                            if playerNum == game['targetPlayerNum']:
                                # 手牌を変換する
                                kyoku['lastTehais'][playerNum].sort()
                                man = ''
                                pin = ''
                                sou = ''
                                honors = ''
                                for pai in kyoku['lastTehais'][playerNum]:
                                    pai = convertPai(pai)
                                    paishu = pai[-1]
                                    if paishu == "m":
                                        man += pai[:-1]
                                    elif paishu == "p":
                                        pin += pai[:-1]
                                    elif paishu == "s":
                                        sou += pai[:-1]
                                    elif paishu == "z":
                                        honors += pai[:-1]

                                # 対子の数を数える
                                def count_pair(string):
                                    # 同じ文字を2回以上使っているものの種類数を数える
                                    return sum(1 for char in set(string) if string.count(char) >= 2)

                                man_pair_count = count_pair(man)
                                pin_pair_count = count_pair(pin)
                                sou_pair_count = count_pair(sou)
                                honors_pair_count = count_pair(honors)
                                pair_count = man_pair_count + pin_pair_count + sou_pair_count + honors_pair_count

                                # 手牌が4対子の場合
                                if pair_count == 4:
                                    # 該当局面をcsvに出力する

                                    # 局数（東●局）
                                    kyokuStr = "東1局"
                                    if kyoku['seed'][0] < 4:
                                        kyokuStr = "東"+str(kyoku['seed'][0]+1)+"局"
                                    elif kyoku['seed'][0] < 8:
                                        kyokuStr = "南"+str(kyoku['seed'][0] % 4+1)+"局"
                                    elif kyoku['seed'][0] < 12:
                                        kyokuStr = "西"+str(kyoku['seed'][0] % 4+1)+"局"
                                    elif kyoku['seed'][0] < 16:
                                        kyokuStr = "北"+str(kyoku['seed'][0] % 4+1)+"局"

                                    # 自風
                                    jikazeNum = (kyoku['seed'][0] % 4 + game['targetPlayerNum']) % 4
                                    jikaze = ["東", "南", "西", "北"][jikazeNum]

                                    # 鳴き有無
                                    nakiFlg = kyoku['flgNaki'][game['targetPlayerNum']]
                                    # print(kyokuStr)
                                    # print(kyoku['ten'][playerNum])
                                    # print(game['url']+"&ts="+str(kyoku['ts'])+"&tj="+str(kyoku['tj']))

                                    # csvでの出力文字列を作成しresultsに追加(局、持ち点、自風、鳴き有無、URL)
                                    result = [kyokuStr, kyoku['ten'][playerNum], jikaze, nakiFlg,
                                              '=HYPERLINK("'+game['url']+"&ts="+str(kyoku['ts'])+"&tj="+str(kyoku['tj'])+'")']
                                    results.append(result)

                                    # 該当局面が抽出されたらその局の処理を終了する
                                    kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1


                                # 先制リーチを受けている
                                if 1 in kyoku['flgReach']:
                                    # 処理を終了する
                                    kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1
                                    break
                                    # 更新用に下記の未使用のコードは残しておく

                                    # if kyokuNum == 0: # バグ改修用
                                    #     print(kyoku['flgReach'])

                                    # 手牌を変換する
                                    kyoku['lastTehais'][playerNum].sort()
                                    man = ''
                                    pin = ''
                                    sou = ''
                                    honors = ''
                                    for pai in kyoku['lastTehais'][playerNum]:
                                        pai = convertPai(pai)
                                        paishu = pai[-1]
                                        if paishu == "m":
                                            man += pai[:-1]
                                        elif paishu == "p":
                                            pin += pai[:-1]
                                        elif paishu == "s":
                                            sou += pai[:-1]
                                        elif paishu == "z":
                                            honors += pai[:-1]

                                    # 手牌14枚でイーシャンテンだった場合
                                    shanten = Shanten()
                                    tiles = TilesConverter.string_to_34_array(man=man, pin=pin, sou=sou, honors=honors)
                                    result = shanten.calculate_shanten(tiles)
                                    # if kyokuNum == 0:  # バグ修正用
                                    #     print(result)
                                    #     print(man+pin+sou+honors)

                                    if result == 1:
                                        # 局数（東●局）
                                        kyokuStr = "東1局"
                                        if kyoku['seed'][0] < 4:
                                            kyokuStr = "東"+str(kyoku['seed'][0]+1)+"局"
                                        elif kyoku['seed'][0] < 8:
                                            kyokuStr = "南"+str(kyoku['seed'][0] % 4+1)+"局"
                                        elif kyoku['seed'][0] < 12:
                                            kyokuStr = "西"+str(kyoku['seed'][0] % 4+1)+"局"
                                        elif kyoku['seed'][0] < 16:
                                            kyokuStr = "北"+str(kyoku['seed'][0] % 4+1)+"局"

                                        # 自風
                                        jikazeNum = (kyoku['seed'][0] % 4 + game['targetPlayerNum']) % 4
                                        jikaze = ["東", "南", "西", "北"][jikazeNum]

                                        # 鳴き有無
                                        nakiFlg = kyoku['flgNaki'][game['targetPlayerNum']]
                                        # print(kyokuStr)
                                        # print(kyoku['ten'][playerNum])
                                        # print(game['url']+"&ts="+str(kyoku['ts'])+"&tj="+str(kyoku['tj']))

                                        # csvでの出力文字列を作成しresultsに追加(局、持ち点、自風、鳴き有無、URL)
                                        result = [kyokuStr, kyoku['ten'][playerNum], jikaze, nakiFlg,
                                                  '=HYPERLINK("'+game['url']+"&ts="+str(kyoku['ts'])+"&tj="+str(kyoku['tj'])+'")']
                                        results.append(result)

                                        # 該当局面が抽出されたらその局の処理を終了する
                                        kyoku['flgCheckEnd'][game['targetPlayerNum']] = 1

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
    # 進捗表示
    print(str(index+1)+" / "+str(len(listFiles)))

# 現在のPythonファイル名を取得し、拡張子を.csvに変更
csv_filename = os.path.splitext(os.path.basename(__file__))[0] + '.csv'

with open(csv_filename, 'w', newline="") as f:
    writer = csv.writer(f)
    writer.writerows(results)
