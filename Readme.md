# 牌譜解析

## 概要

AI の牌譜解析で過去に作ったものをまとめました

## ファイル構成

- getHaihuUrl.py
  html ファイルから牌譜 URL を抽出し、URL のリストを CSV ファイルとして保存する

- getHaihuText.py
  CSV ファイルに保存された牌譜 URL をもとに、tenhou.net から牌譜を取得し、ローカルに保存する

- mj_function.py
  麻雀牌譜解析に必要な関数をまとめたファイル

- stats.py
  牌譜データをもとに、指定した天鳳 ID の麻雀牌譜解析結果を出力する

- tenpai.py
  牌譜データをもとに、指定した天鳳 ID のテンパイ時の牌譜 URL を CSV で出力する

- shanten.py
  牌譜データをもとに、指定した天鳳 ID のイーシャンテン時の牌譜 URL を CSV で出力する
