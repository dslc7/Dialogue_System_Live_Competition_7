<!-- ![Color logo with background](https://github.com/remdis/remdis/assets/15374299/da5eb1c0-b3b4-4056-9c68-99448265e9a4) -->

# [対話システムライブコンペ 7](https://sites.google.com/view/dslc7)配布ソフトウェア

対話システムライブコンペ 7 では，[Remdis](https://github.com/remdis/remdis)をベースとしたシステムを使用します．

## 必要環境

- Docker

## インストール方法

### Step 1. Remdis 本体のインストール

> [!NOTE]
> 本リポジトリでは Git lfs を使用します。未インストールの方はこちらの[リンク](https://docs.github.com/ja/repositories/working-with-files/managing-large-files/installing-git-large-file-storage)等を参考に Git lfs をインストールしてください。

#### Clone

```bash
git clone --recursive https://github.com/p1n0k0/Dialogue_System_Live_Competition_7.git
cd Dialogue_System_Live_Competition_7
git submodule init
git submodule update
```

#### Docker ファイルのビルド

```bash
cd docker

# タスクトラックの開発者向け
docker compose -f docker-compose.dev.yaml build

# シチュエーショントラックの開発者向け
docker compose -f docker-compose.prompt-only.yaml build
```

Windows を使用している方は追加で以下を実行してください。

```bash
sed -i 's/\r//g' run.sh

# 上記コマンドが必要なのはなぜ？
# Windowsは改行コードが\r\nですが、UbuntuなどのUNIXでは\nのため、
# 次のようなエラーが発生しうるためです。
# $’\r’: command not found
```

### Step 2. MMDAgent-EX のインストール (Windows 以外)

- Windows 以外の OS は，[MMDAgent-EX 公式サイト](https://mmdagent-ex.dev/ja/)の[入手とビルド](https://mmdagent-ex.dev/ja/docs/build/) に従って MMDAgent-EX をインストール
- Windows はそのまま次へ（実行バイナリが同梱されているので手順不要）

### Step 3. 各種 API 鍵の取得と設定

- Google Speech Cloud API の API 鍵を JSON 形式で取得し，config/config.yaml の下記部分にパスを記載
  ```
  ASR:
   ...
   json_key: <enter your API key>
  ```
  Docker を使用している場合、JSON ファイルを config 配下に配置するとマウントされます。その場合のファイルパスは`/home/ubuntu/dslc7/config/<file>.json`です。
- OpenAI の API 鍵を取得し，config/config.yaml の下記部分に記載
  ```
  ChatGPT:
    api_key: <enter your API key>
  ```
- Azure TTS の API 鍵を取得し，config/config.yaml の下記部分に記載
  ```
  azure: # This option is only used when "engine_name" is "azure". Otherwise, no setting is required.
    api_key: <enter your azure API key>
    region: <enter your azure region> # <-- japaneast or japanwest
  ```

## 利用方法

### Remdis の実行

```bash
cd docker

# タスクトラックの場合
sh scripts/run_task.sh

# シチュエーショントラックの場合
sh scripts/run_situation.sh
```

### 音声/動画入力サーバの起動

- Windows の場合
  エクスプローラから`remdis-tools/input.exe`を実行
- Mac の場合
  Finder から`remdis-tools/input`を実行

使用したい音声/動画の入力デバイスの番号が、環境により異なることがあります。  
そのため、`config/config.yaml`において、環境に合わせて設定できます。以下は、0 番からそれぞれ使用するデバイス番号を 1 にする変更です。

```diff
AIN:
  frame_length: 0.005 # sec
  sample_rate: 16000 # Hz
  sample_width: 2 # Bytes
  num_channel: 1
-  device_index: 0
+  device_index: 1

VIN:
-  device_index: 0
+  device_index: 1
```

また、MacOS では ffmpeg を用いて、容易にデバイスの番号を確かめることができます。（出力はあくまでも一例です）

```sh
ffmpeg -f avfoundation -list_devices true -i ""
ffmpeg version 7.0.2 Copyright (c) 2000-2024 the FFmpeg developers
  built with Apple clang version 15.0.0 (clang-1500.3.9.4)
  configuration: --prefix=/opt/homebrew/Cellar/ffmpeg/7.0.2 --enable-shared --enable-pthreads --enable-version3 --cc=clang --host-cflags= --host-ldflags='-Wl,-ld_classic' --enable-ffplay --enable-gnutls --enable-gpl --enable-libaom --enable-libaribb24 --enable-libbluray --enable-libdav1d --enable-libharfbuzz --enable-libjxl --enable-libmp3lame --enable-libopus --enable-librav1e --enable-librist --enable-librubberband --enable-libsnappy --enable-libsrt --enable-libssh --enable-libsvtav1 --enable-libtesseract --enable-libtheora --enable-libvidstab --enable-libvmaf --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxml2 --enable-libxvid --enable-lzma --enable-libfontconfig --enable-libfreetype --enable-frei0r --enable-libass --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenjpeg --enable-libspeex --enable-libsoxr --enable-libzmq --enable-libzimg --disable-libjack --disable-indev=jack --enable-videotoolbox --enable-audiotoolbox --enable-neon
  libavutil      59.  8.100 / 59.  8.100
  libavcodec     61.  3.100 / 61.  3.100
  libavformat    61.  1.100 / 61.  1.100
  libavdevice    61.  1.100 / 61.  1.100
  libavfilter    10.  1.100 / 10.  1.100
  libswscale      8.  1.100 /  8.  1.100
  libswresample   5.  1.100 /  5.  1.100
  libpostproc    58.  1.100 / 58.  1.100
2024-11-27 22:08:41.830 ffmpeg[85651:2901202] WARNING: Add NSCameraUseContinuityCameraDeviceType to your Info.plist to use AVCaptureDeviceTypeContinuityCamera.
2024-11-27 22:08:42.058 ffmpeg[85651:2901202] WARNING: AVCaptureDeviceTypeExternal is deprecated for Continuity Cameras. Please use AVCaptureDeviceTypeContinuityCamera and add NSCameraUseContinuityCameraDeviceType to your Info.plist.
[AVFoundation indev @ 0x14e705a60] AVFoundation video devices:
[AVFoundation indev @ 0x14e705a60] [0] FaceTime HDカメラ
[AVFoundation indev @ 0x14e705a60] AVFoundation audio devices:
[AVFoundation indev @ 0x14e705a60] [0] Background Music
[AVFoundation indev @ 0x14e705a60] [1] MacBook Proのマイク
[AVFoundation indev @ 0x14e705a60] [2] Background Music (UI Sounds)
[AVFoundation indev @ 0x14e705a60] [3] ZoomAudioDevice
```

### Travel Viewer を動かしてみる

Travel Viewer は以下の URL で公開されています。

- App: https://dslc7.github.io/travel-viewer/
- Repo: https://github.com/dslc7/travel-viewer

アプリを開き、`ws://localhost:9999` を設定し、CONNECT を押下してください。その後、以下のスクリプトを実行してください。

- [`scripts/run_sample_travel_viewer.sh`](scripts/run_sample_travel_viewer.sh) を実行
  ```sh
  docker compose -f docker-compose.dev.yaml exec remdis  bash scripts/run_sample_travel_viewer.sh
  ```

## TIPS

### `RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory`のエラーで、`video_processor`が進まない

`video_processor.py`の初回実行時には、多くのプログレスバーが出てきます。  
これは、画像認識モデルの重みをダウンロードしているためです。

このたくさんのダウンロードが起きている途中でプロセスを切ってしまうと、`RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory`というエラーが出るようになり、ずっと実行できなくなる可能性があります。

`py-feat`を再インストールすると修正できる可能性があります。
以下のようにして、docker container 内の環境から、`py-feat`を再インストールすると良いでしょう。

```bash
$ docker compose -f docker-compose.dev.yaml exec remdis bash
# ここからコンテナ内
$ pip uninstall py-feat
$ pip install py-feat
```

### マイクとスピーカーが正しく接続されているか確認したい

- chk_mic_spk.py を実行
  ```
  # 自分の発話がフィードバックされて聴こえていればOK
  python input.py
  python chk_mic_spk.py
  python output.py
  ```

### 一定時間が経過したらシステム側から話しかけるようにしたい

- time_out.py を実行
  ```
  # テキスト対話の例
  python tin.py
  python dialogue.py
  python tout.py
  python time_out.py
  ```

## 開発時の参考情報

### 入力情報・形式

ユーザの音声と映像から発話文・顔向き・感情を取得します．取得された顔向きと感情は，離散化（顔向き：右向き・左向き・うなずき・首をかしげる・正面，感情：怒り・嫌悪・恐怖・幸福・悲しみ・驚き・中立）され，発話文/感情/顔向きの形で LLM に入力されます．

### CG アバターのモーションについて

現在はプロンプト中に記述されている以下の標準で定義されている感情と動きに対応しています．今後はなるべく早くより多様なモーションに対応する予定です．

感情：平静・喜び・感動・納得・考え中・眠い・ジト目・同情・恥ずかしい・怒り

動き：待機・ユーザの声に気づく・うなずく・首をかしげる・考え中・会釈・お辞儀・片手を振る・両手を振る・見渡す

### TTS の出力スタイルについて

TTS の出力スタイルを発話にあわせて chat・cheerful・customerservice の 3 つからプロンプトを用いて動的に変更することができます．TTS のスタイルを変更したい場合は config/config.yaml の ChatGPT 内の output_tts_style を on に、prompts 内の RESP を prompt/response_w_tts_style.txt に変更してください．

## ライセンス

### 外部パッケージの利用規約

本ソフトウェアでは，音声認識に[Google Cloud Speech-to-Text API](https://cloud.google.com/speech-to-text?hl=ja)，音声合成に[Azure Text-to-Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech)，対話生成に[OpenAI API](https://openai.com/blog/openai-api)，顔画像処理に[Py-feat](https://github.com/cosanlab/py-feat)及び[Py-feat 内のモデル](https://github.com/cosanlab/py-feat?tab=License-1-ov-file)といった外部パッケージを利用します．
ライセンスに関してはそれぞれのパッケージの利用規約をご参照ください．

## References

### Remdis

```
@inproceedings{remdis2024iwsds,
  title={The Remdis toolkit: Building advanced real-time multimodal dialogue systems with incremental processing and large language models},
  author={Chiba, Yuya and Mitsuda, Koh and Lee, Akinobu and Higashinaka, Ryuichiro},
  booktitle={Proc. IWSDS},
  pages={1--6},
  year={2024},
}
```

```
@inproceedings{remdis2023slud,
  title={Remdis: リアルタイムマルチモーダル対話システム構築ツールキット},
  author={千葉祐弥 and 光田航 and 李晃伸 and 東中竜一郎},
  booktitle={人工知能学会 言語・音声理解と対話処理研究会（第99回）},
  pages={25--30},
  year={2023},
}
```

### 対話システムライブコンペティション 7

**シチュエーショントラック**

```
@inproceedings{livecompe-situation2025sigdial,
  title={Analyzing Dialogue System Behavior in a Specific Situation Requiring Interpersonal Consideration},
  author={Takahashi, Tetsuro and Kikuchi, Hirofumi and Yang,Jie and Nishikawa, Hiroyuki and Komuro, Masato and Makino, Ryosaku and Sato, Shiki and Sasaki, Yuta and Iwata, Shinji and Hentona, Asahi and Yamazaki, Takato and Moriya, Shoji and Ohagi, Masaya and Qi, Zhiyang and Kodama, Takashi and Lee, Akinobu and Minato, Takashi and Sakai, Kurima and Funayama, Tomo and Funakoshi, Kotaro and Usami, Mayumi and Inaba,Michimasa and Higashinaka, Ryuichiro},
  booktitle={Proceedings of the 26th Annual Meeting of the Special Interest Group on Discourse and Dialogue},
  year={2025},
}
```

**タスクトラック**

```
@inproceedings{livecompe-task2025sigdial,
  title={Key Challenges in Multimodal Task-Oriented Dialogue Systems: Insights from a Large Competition-Based Dataset},
  author={Sato, Shiki and Iwata, Shinji and Hentona, Asahi and Sasaki, Yuta and Yamazaki, Takato and Moriya, Shoji and Ohagi, Masaya and Kikuchi, Hirofumi and Yang, Jie and Qi, Zhiyang and Kodama, Takashi and Lee, Akinobu and Komuro, Masato and Nishikawa, Hiroyuki and Makino, Ryosaku and Minato, Takashi and Sakai, Kurima and Funayama, Tomo and Funakoshi, Kotaro and Usami, Mayumi and Inaba, Michimasa and Takahashi, Tetsuro and Higashinaka, Ryuichiro},
  booktitle={Proceedings of the 26th Annual Meeting of the Special Interest Group on Discourse and Dialogue},
  year={2025},
}
```
