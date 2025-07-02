# 対話システム ライブコンペ用 MMDAgent-EX セット for Remdis

## 利用方法

このフォルダの中身を全て Remdis の `MMDAgent-EX` フォルダ以下に上書きコピーして、以下のどちらかを起動する。

- `run_situtaion.vbs`: シチュエーショントラック用アセットで起動
- `run_task.vbs`: タスクトラック用アセットで起動

## テスト

数字キー `1` から `6` で同梱のモーションを試せる。

- `1`: 会釈
- `2`: おじぎ
- `3`: 考え中
- `4`: 片手を振る
- `5`: 両手を振る
- `6`: 右手を添えて説明

## ファイル

シチュエーショントラック用ファイル

- `situation.mdf`: 起動ファイル
- `situation.fst`: メインFSTスクリプト
- `situation.fst.base.fst`: サブFSTスクリプト１（基本姿勢を一定時間ごとに変更）
- `situation.fst.blink.fst`: サブFSTスクリプト２（一定時間ごとにまばたき）

タスクトラック用ファイル

- `task.mdf`: 起動ファイル
- `task.fst`: メインFSTスクリプト
- `task.fst.blink.fst`: サブFSTスクリプト２（一定時間ごとにまばたき）

実行ファイル

- `bin`: MMDAgent-EX の実行セット（作成時点での最新版に更新済み）

アセット（画像・モーション・モデル等）

- `asset`: 画像・モーション・モデルファイル等

## 画像を変える

`situation.fst` あるいは `task.fst` の冒頭の画像ファイルの指定を変更する。
`${cg_model}` がCGモデル（.pmdファイル）、 `${background_image}` が背景画像、`${frame_image}` が前景画像。

```text
${cg_model}=asset/models/uka/MS_Uka_Humanify.pmd

${background_image}=asset/images/bg_cafe.png

${frame_image}=asset/images/desk_front.png
```

背景画像は 16 : 9 の画像を使うこと。jpeg, png が使用可能。

前景画像は PNG 形式。抜きたい部分を透過で作る。

## その他

- situtation では、一定時間ごとにCGエージェントの待ちモーションが切り替わるようになっている。これを無効化するには`situation.fst.base.fst` を削除する。
- カメラ位置の調整は、各 .fst の `CAMERA` メッセージで行っている。
- その他、詳細は MMDAgent-EX のドキュメントサイトを参考にすること。

## ライセンス表記
このソフトウェアは、 [Apache 2.0ライセンス](https://www.apache.org/licenses/LICENSE-2.0)で配布されている製作物が含まれています。
