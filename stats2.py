# import glob
import pathlib
import csv
import os
import numpy as np
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# 自作関数
from mj_function import convertPai, getDoraStr

# 定数定義
class Constants:
    TARGET_FOLDER = "luckyj"
    TARGET_PLAYER_NAME = "%E2%93%9D%4C%75%63%6B%79%4A"
    BASE_URL = "https://tenhou.net/5/?log="

@dataclass
class GameInfo:
    name: str = "TAIKYOKU"
    id: str = ""
    type: int = 0
    oya: int = 0
    kyokus: List[Dict] = field(default_factory=list)
    target: List = field(default_factory=list)
    target_player_num: int = 99
    url: str = ""

class MahjongLogParser:
    """麻雀ログの解析を行うクラス"""
    def __init__(self):
        self.results = []
        
    def parse_files(self) -> None:
        """ファイルを解析してデータを収集"""
        files = list(pathlib.Path(Constants.TARGET_FOLDER).glob('*.txt'))
        for index, file_path in enumerate(files):
            game = self._parse_single_file(file_path)
            self._analyze_game(game)
            print(f"{index+1} / {len(files)}")  # 進捗表示

    def _parse_single_file(self, file_path: pathlib.Path) -> GameInfo:
        """単一のファイルを解析"""
        with open(file_path) as f:
            content = f.read()
            game_id = str(file_path)[7:-4]
            
            # mjlogのタグを削除して分割
            content = content[20:-12]
            tags = content.split("/><")
            
            game = GameInfo(id=game_id, url=f"{Constants.BASE_URL}{game_id}")
            
            for tag in tags:
                self._process_tag(tag, game)
                
            return game

    def _parse_attributes(self, tag: str) -> Dict[str, Any]:
        """タグの属性をパースする"""
        attrs = {}
        parts = tag.split()
        for part in parts[1:]:  # 最初の要素（タグ名）をスキップ
            if "=" in part:
                key, value = part.split("=")
                # 数値の場合は変換
                try:
                    value = int(value.strip('"'))
                except ValueError:
                    value = value.strip('"')
                attrs[key] = value
        return attrs

    def _process_tag(self, tag: str, game: GameInfo) -> None:
        """タグの処理"""
        if not tag:
            return
            
        tag_type = tag.split(" ")[0]
        tag_handlers = {
            'SHUFFLE': self._handle_shuffle,
            'GO': self._handle_go,
            'UN': self._handle_un,
            'INIT': self._handle_init,
            'AGARI': self._handle_agari,
            'RYUUKYOKU': self._handle_ryuukyoku,
            'REACH': self._handle_reach
        }
        
        handler = tag_handlers.get(tag_type)
        if handler:
            handler(tag, game)

    def _handle_shuffle(self, tag: str, game: GameInfo) -> None:
        """シャッフルタグの処理"""
        attrs = self._parse_attributes(tag)
        # シャッフル情報の処理（必要に応じて実装）
        pass

    def _handle_go(self, tag: str, game: GameInfo) -> None:
        """GOタグの処理"""
        attrs = self._parse_attributes(tag)
        if 'type' in attrs:
            game.type = attrs['type']

    def _handle_un(self, tag: str, game: GameInfo) -> None:
        """UNタグ（プレイヤー情報）の処理"""
        attrs = self._parse_attributes(tag)
        for i in range(4):
            name_key = f"n{i}"
            if name_key in attrs and attrs[name_key] == Constants.TARGET_PLAYER_NAME:
                game.target_player_num = i

    def _handle_init(self, tag: str, game: GameInfo) -> None:
        """INITタグ（局の初期状態）の処理"""
        attrs = self._parse_attributes(tag)
        kyoku_info = {
            'round': attrs.get('seed', 0),
            'score': attrs.get('ten', '').split(','),
            'hands': attrs.get('hai0', '').split(','),
            'result': None
        }
        game.kyokus.append(kyoku_info)
        game.oya = attrs.get('oya', 0)

    def _handle_agari(self, tag: str, game: GameInfo) -> None:
        """AGARIタグ（和了）の処理"""
        attrs = self._parse_attributes(tag)
        if game.kyokus:
            current_kyoku = game.kyokus[-1]
            current_kyoku['result'] = {
                'type': 'agari',
                'who': attrs.get('who', -1),
                'from': attrs.get('fromWho', -1),
                'score': attrs.get('ten', '').split(','),
                'yaku': attrs.get('yaku', '').split(',')
            }

    def _handle_ryuukyoku(self, tag: str, game: GameInfo) -> None:
        """RYUUKYOKUタグ（流局）の処理"""
        attrs = self._parse_attributes(tag)
        if game.kyokus:
            current_kyoku = game.kyokus[-1]
            current_kyoku['result'] = {
                'type': 'ryuukyoku',
                'reason': attrs.get('type', 'normal')
            }

    def _handle_reach(self, tag: str, game: GameInfo) -> None:
        """REACHタグ（立直）の処理"""
        attrs = self._parse_attributes(tag)
        if game.kyokus:
            current_kyoku = game.kyokus[-1]
            if 'reach' not in current_kyoku:
                current_kyoku['reach'] = []
            current_kyoku['reach'].append({
                'who': attrs.get('who', -1),
                'step': attrs.get('step', 1)
            })

    def _analyze_game(self, game: GameInfo) -> None:
        """ゲームの分析を行う"""
        for kyoku in game.kyokus:
            self._analyze_kyoku(kyoku, game)

    def _analyze_kyoku(self, kyoku: Dict, game: GameInfo) -> None:
        """局の分析を行う"""
        # 分析結果をself.resultsに追加
        result_row = [
            game.id,
            game.url,
            kyoku.get('round', 0),
            game.target_player_num,
            kyoku.get('result', {}).get('type', 'unknown')
        ]
        self.results.append(result_row)

    def save_results(self) -> None:
        """結果をCSVファイルに保存"""
        csv_filename = os.path.splitext(os.path.basename(__file__))[0] + '.csv'
        headers = ['Game ID', 'URL', 'Round', 'Target Player', 'Result Type']
        
        with open(csv_filename, 'w', newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(self.results)

def main():
    """
    麻雀ログの解析を実行し、結果をCSVファイルに保存する
    
    処理内容:
    1. MahjongLogParserインスタンスを作成
    2. ログファイルの解析を実行
    3. 解析結果をCSVファイルに出力
    """
    parser = MahjongLogParser()
    parser.parse_files()
    parser.save_results()

if __name__ == "__main__":
    main()
