# Docker for DSLC7

## 各ファイルの説明

### `docker-compose.prompt-only.yaml`: シチュエーショントラック開発者向け

プロンプトのみ変更可能なシチュエーショントラックに合わせた設定です。既にアップロードされているビルド済みのイメージを使用しています。

```sh
# 起動 (実行はしません)
docker compose -f docker-compose.prompt-only.yaml up -d
# 実行
docker compose -f docker-compose.prompt-only.yaml exec remdis bash run.sh
```

### `docker-compose.dev.yaml`: タスクトラック開発者向け

ローカルのディレクトリをマウントします。開発時に使用してください。

```sh
# ビルド
docker compose -f docker-compose.dev.yaml build
# 起動 (実行はしません)
docker compose -f docker-compose.dev.yaml up -d
# 実行
docker compose -f docker-compose.dev.yaml exec remdis bash run.sh
# コンテナに入る
docker compose -f docker-compose.dev.yaml exec remdis bash
```

### `docker-compose.prod.yaml`: 本番・本番用テスト向け (後日配布)

本番で使用する設定です。

```sh
# ビルド
docker compose -f docker-compose.prod.yaml build
# 実行
docker compose -f docker-compose.prod.yaml up -d
```
