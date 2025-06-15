import queue
import random
import sys
import threading
import time

import prompt_util as prompt_util
from base import RemdisModule, RemdisState, RemdisUpdateType, RemdisUtil
from llm import ResponseChatGPT

STYLES = ["chat", "cheerful", "customerservice"]
# MMDAgentEXLabel --> LLM input format
EXPRESSIONS = {
    "normal": "0_平静",
    "joy": "1_喜び",
    "impressed": "2_感動",
    "convinced": "3_納得",
    "thinking": "4_考え中",
    "sleepy": "5_眠い",
    "suspicion": "6_ジト目",
    "compassion": "7_同情",
    "embarrassing": "8_恥ずかしい",
    "anger": "9_怒り",
}
ACTIONS = {
    "wait": "0_待機",
    "listening": "1_ユーザの声に気づく",
    "nod": "2_うなずく",
    "head_tilt": "3_首をかしげる",
    "thinking": "4_考え中",
    "light_greeting": "5_会釈",
    "greeting": "6_お辞儀",
    "wavehand": "7_片手を振る",
    "wavehands": "8_両手を振る",
    "lookaround": "9_見渡す",
}


class Dialogue(RemdisModule):
    def __init__(
        self,
        pub_exchanges=["dialogue", "dialogue2"],
        sub_exchanges=["asr", "video_process", "vap", "tts", "bc", "emo_act"],
    ):
        super().__init__(pub_exchanges=pub_exchanges, sub_exchanges=sub_exchanges)

        # 設定の読み込み
        self.history_length = self.config["DIALOGUE"]["history_length"]
        self.response_generation_interval = self.config["DIALOGUE"][
            "response_generation_interval"
        ]
        self.prompts = prompt_util.load_prompts(self.config["ChatGPT"]["prompts"])
        # コンペティション別の設定読み込み
        self.dialogue_duration = self.config["COMPETITION"]["duration"]  # 対話時間
        self.uttrance_to_terminate = self.config["COMPETITION"][
            "utterance_to_terminate"
        ]  # 終了発話
        self.initial_utterances: list[str] | str = self.config["COMPETITION"][
            "initial_utterance"
        ]
        self.system_first: bool = self.config["COMPETITION"]["system_first"]

        self.output_format: str = (
            "{style}/{response}/{expression},{action}"
            if self.config["ChatGPT"]["output_tts_style"]
            else "{response}/{expression},{action}"
        )

        # 対話履歴
        self.dialogue_history = []

        # IUおよび応答の処理用バッファ
        self.system_utterance_end_time = 0.0
        self.input_iu_buffer = queue.Queue()
        self.input_iu_video_buffer = queue.Queue()
        self.bc_iu_buffer = queue.Queue()
        self.emo_act_iu_buffer = queue.Queue()
        self.output_iu_buffer = []
        self.llm_buffer = queue.Queue()

        # 対話状態管理
        self.event_queue = queue.Queue()
        self.state = "idle"

        self._is_running = False  # 起動時はOFF
        self.system_start = time.perf_counter()  # システム開始時刻

        # IU処理用の関数
        self.util_func = RemdisUtil()

    # メインループ
    def run(self):
        # 音声認識結果受信スレッド
        t1 = threading.Thread(target=self.listen_asr_loop)
        # 音声合成結果受信スレッド
        t2 = threading.Thread(target=self.listen_tts_loop)
        # ターンテイキングイベント受信スレッド
        t3 = threading.Thread(target=self.listen_vap_loop)
        # 相槌生成結果受信スレッド
        t4 = threading.Thread(target=self.listen_bc_loop)
        # 表情・行動情報受信スレッド
        t5 = threading.Thread(target=self.listen_emo_act_loop)
        # 逐次応答生成スレッド
        t6 = threading.Thread(target=self.parallel_response_generation)
        # 状態制御スレッド
        t7 = threading.Thread(target=self.state_management)
        # 表情・行動制御スレッド
        t8 = threading.Thread(target=self.emo_act_management)
        # 動画像処理スレッド（追加の関係上、t9として追加）
        t9 = threading.Thread(target=self.listen_video_process_loop)

        # スレッド実行
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t5.start()
        t6.start()
        t7.start()
        t8.start()
        t9.start()

    # 音声認識結果受信用のコールバックを登録
    def listen_asr_loop(self):
        self.subscribe("asr", self.callback_asr)

    # 動画像処理結果受信用のコールバックを登録
    def listen_video_process_loop(self):
        self.subscribe("video_process", self.callback_video_process)

    # 音声合成結果受信用のコールバックを登録
    def listen_tts_loop(self):
        self.subscribe("tts", self.callback_tts)

    # VAP情報受信用のコールバックを登録
    def listen_vap_loop(self):
        self.subscribe("vap", self.callback_vap)

    # バックチャネル受信用のコールバックを登録
    def listen_bc_loop(self):
        self.subscribe("bc", self.callback_bc)

    # 表情・行動情報受信用のコールバックを登録
    def listen_emo_act_loop(self):
        self.subscribe("emo_act", self.callback_emo_act)

    # 随時受信される音声認識結果に対して並列に応答を生成
    def parallel_response_generation(self):
        # 受信したIUを保持しておく変数
        iu_memory = []
        iu_video_memory = []
        new_iu_count = 0

        input_iu_video = None
        while True:  # ASR-drivenでの処理
            # [最新の]IUを受信して保存
            input_iu = None
            while not self.input_iu_buffer.empty():
                input_iu = self.input_iu_buffer.get(block=False)
                iu_memory.append(input_iu)
                # IUがREVOKEだった場合はメモリから削除
                iu_memory = self.util_func.remove_revoked_ius(iu_memory)

            while not self.input_iu_video_buffer.empty():
                input_iu_video = self.input_iu_video_buffer.get(block=False)
                iu_video_memory.append(input_iu_video)
                # IUがREVOKEだった場合はメモリから削除
                iu_video_memory = self.util_func.remove_revoked_ius(iu_video_memory)

            if input_iu is None:  # 音声認識結果のキューが溜まっていなかったらパス
                continue
            # ADD/COMMITの場合は応答候補生成
            if input_iu["update_type"] != RemdisUpdateType.REVOKE:
                user_utterance = self.util_func.concat_ius_body(iu_memory)
                if user_utterance == "":
                    continue
                raw_utterance = user_utterance
                if len(iu_video_memory):
                    video_info = iu_video_memory[-1]["body"]
                    user_utterance = (
                        f"{user_utterance}/感情:{video_info[0]}/顔向き:{video_info[1]}"
                    )
                # ADDの場合は閾値以上のIUが溜まっているか確認し，溜まっていなければ次のIUもしくはCOMMITを待つ
                if (
                    input_iu["update_type"] == RemdisUpdateType.ADD
                    and "（沈黙）" not in user_utterance
                ):
                    new_iu_count += 1
                    if new_iu_count < self.response_generation_interval:
                        continue
                    else:
                        new_iu_count = 0

                # TODO: リッチな対話終了処理
                # 初期実装としての強制終了
                if (
                    self._is_running
                    and time.perf_counter() - self.system_start > self.dialogue_duration
                ):
                    self.terminate_dialogue(self.uttrance_to_terminate)
                    continue  # self.terminate_dialogueとcontinueの2行はセットを推奨

                # TODO: リッチな対話開始処理
                if not self._is_running:  # システムが起動していない時
                    if input_iu["update_type"] != RemdisUpdateType.COMMIT:
                        continue
                    if ("システムリセット" in raw_utterance) or (
                        "システムリリセット" in raw_utterance  # hacky
                    ):  # 「システムリセット」なら起動
                        # システムの初期化と対話開始のお知らせ
                        self._is_running = True
                        self.publish(
                            self.createIU(
                                "システムをリセットしました",
                                "dialogue",
                                RemdisUpdateType.COMMIT,
                            ),
                            "dialogue",
                        )
                        new_iu_count = 0
                        iu_memory = []
                        self.dialogue_history = []
                        self.system_start = time.perf_counter()
                        if self.system_first:
                            self._start_from_system()
                        continue

                    # 「システムリセット」でない場合は、開始方法をインストラクション
                    self.publish(
                        self.createIU(
                            "システムリセットと発話して、システムを起動してください。",
                            "dialogue",
                            RemdisUpdateType.ADD,
                        ),
                        "dialogue",
                    )
                    self.publish(
                        self.createIU("", "dialogue", RemdisUpdateType.COMMIT),
                        "dialogue",
                    )
                    continue
                else:  # システム起動中だが、「システムリセット」を発話された時
                    if ("システムリセット" in raw_utterance) or (
                        "システムリリセット" in raw_utterance  # hacky
                    ):  # 「システムリセット」なら起動
                        # システムの初期化と対話開始のお知らせ
                        self._is_running = True
                        self.publish(
                            self.createIU(
                                "対話を終了し、システムをリセットしました",
                                "dialogue",
                                RemdisUpdateType.COMMIT,
                            ),
                            "dialogue",
                        )
                        self.dialogue_history = []
                        self.system_start = time.perf_counter()
                        new_iu_count = 0
                        iu_memory = []
                        if self.system_first:
                            self._start_from_system()
                        continue

                # パラレルな応答生成処理
                # 応答がはじまったらLLM自体がbufferに格納される
                print("\033[33mStart LLM >>>")
                print(f"{user_utterance=}")
                print(f"{self.dialogue_history=}")
                llm = ResponseChatGPT(self.config, self.prompts)
                last_asr_iu_id = input_iu["id"]
                if "（沈黙）" in user_utterance:
                    t = threading.Thread(
                        target=llm.run,
                        args=(
                            input_iu["timestamp"],
                            "",
                            self.dialogue_history,
                            last_asr_iu_id,
                            self.llm_buffer,
                        ),
                        daemon=True,
                    )
                else:
                    t = threading.Thread(
                        target=llm.run,
                        args=(
                            input_iu["timestamp"],
                            user_utterance,
                            self.dialogue_history,
                            last_asr_iu_id,
                            self.llm_buffer,
                        ),
                        daemon=True,
                    )
                print("<<<\033[0m")
                t.start()

                # ユーザ発話終端の処理
                if input_iu["update_type"] == RemdisUpdateType.COMMIT:
                    # ASR_COMMITはユーザ発話が前のシステム発話より時間的に後になる場合だけ発出
                    if self.system_utterance_end_time < input_iu["timestamp"]:
                        self.event_queue.put("ASR_COMMIT")
                    iu_memory = []

    def terminate_dialogue(self, utternance: str):
        self.stop_response()
        self._is_running = False
        self.publish(
            self.createIU(
                utternance,
                "dialogue",
                RemdisUpdateType.COMMIT,
            ),
            "dialogue",
        )
        self.dialogue_history = []  # reset context

    def _start_from_system(self) -> None:
        """対話をシステム発話から開始するときに発火するメソッド"""
        if not isinstance(self.initial_utterances, (str, list)):
            raise RuntimeError(
                "config/config.yamlのCOMPETITION > initial_utteranceは"
                "strもしくはlist[str]です。"
                "例）\n"
                "COMPETITION:\n"
                "   initial_utterance:\n"
                "       - テキスト1\n"
                "       - テキスト2\n"
            )

        if isinstance(self.initial_utterances, list):
            sys_uttr = random.choice(self.initial_utterances)
        else:
            sys_uttr = self.initial_utterances
        # Invoke TTS
        self.publish(
            self.createIU(
                sys_uttr,
                "dialogue",
                RemdisUpdateType.COMMIT,
            ),
            "dialogue",
        )
        # 対話履歴を更新
        self.history_management("assistant", sys_uttr)

    # 対話状態を管理
    def state_management(self):
        while True:
            # イベントに応じて状態を遷移
            event = self.event_queue.get()
            prev_state = self.state
            self.state = RemdisState.transition[self.state][event]
            self.log(
                f"********** State: {prev_state} -> {self.state}, Trigger: {event} **********"
            )

            # 直前の状態がtalkingの場合にイベントに応じて処理を実行
            if prev_state == "talking":
                if event == "SYSTEM_BACKCHANNEL":
                    pass
                if event == "USER_BACKCHANNEL":
                    pass
                if event == "USER_TAKE_TURN":
                    self.stop_response()
                if event == "BOTH_TAKE_TURN":
                    self.stop_response()
                if event == "TTS_COMMIT":
                    self.stop_response()

            # 直前の状態がidleの場合にイベントに応じて処理を実行
            elif prev_state == "idle":
                if event == "SYSTEM_BACKCHANNEL":
                    self.send_backchannel()
                if event == "SYSTEM_TAKE_TURN":
                    self.send_response()
                if event == "ASR_COMMIT":
                    self.send_response()

    # 表情・感情を管理
    def emo_act_management(self):
        while True:
            iu = self.emo_act_iu_buffer.get()
            # 感情または行動の送信
            expression_and_action = {}
            if "expression" in iu["body"]:
                expression_and_action["expression"] = iu["body"]["expression"]
            if "action" in iu["body"]:
                expression_and_action["action"] = iu["body"]["action"]

            if expression_and_action:
                snd_iu = self.createIU(
                    expression_and_action, "dialogue2", RemdisUpdateType.ADD
                )
                snd_iu["data_type"] = "expression_and_action"
                self.printIU(snd_iu)
                self.publish(snd_iu, "dialogue2")

    # システム発話を送信
    def send_response(self):
        # llm bufferが空の間待つ
        while self.llm_buffer.empty():
            print("\033[31mllm buffer is empty, wait 0.1s\033[0m")
            time.sleep(0.1)
        time.sleep(1)
        # 応答が生成され始めたLLMの中で一番新しい音声認識結果を使っているものを選択して送信
        selected_llm = self.llm_buffer.get()
        latest_asr_time = selected_llm.asr_time
        while not self.llm_buffer.empty():
            llm = self.llm_buffer.get()
            if llm.asr_time > latest_asr_time:
                selected_llm = llm

        # IUに分割して送信
        sys.stderr.write(
            "\033[32mResp: Selected user utterance: %s\n\033[0m"
            % (selected_llm.user_utterance)
        )
        if selected_llm.response is not None:
            conc_response = ""
            style = "chat"  # default
            expression = "0_平静"  # default
            action = "0_待機"  # default
            for part in selected_llm.response:
                # 表情・動作を送信
                expression_and_action = {}
                if "expression" in part and part["expression"] != "normal":
                    expression_and_action["expression"] = part["expression"]
                    expression = EXPRESSIONS.get(part["expression"], expression)
                if "action" in part and part["action"] != "wait":
                    expression_and_action["action"] = part["action"]
                    action = ACTIONS.get(part["action"], action)
                if expression_and_action:
                    snd_iu = self.createIU(
                        expression_and_action, "dialogue2", RemdisUpdateType.ADD
                    )
                    snd_iu["data_type"] = "expression_and_action"
                    self.printIU(snd_iu)
                    self.publish(snd_iu, "dialogue2")
                    self.output_iu_buffer.append(snd_iu)
                tts_style = {}
                if "tts_style" in part:
                    tts_style["tts_style"] = part["tts_style"]
                    if part["tts_style"] in STYLES:
                        style = part["tts_style"]
                    snd_iu = self.createIU(tts_style, "dialogue", RemdisUpdateType.ADD)
                    snd_iu["data_type"] = "tts_style"
                    self.printIU(snd_iu)
                    self.publish(snd_iu, "dialogue")
                    self.output_iu_buffer.append(snd_iu)
                # 生成中に状態が変わることがあるためその確認の後，発話を送信
                if "phrase" in part:
                    if self.state == "talking":
                        snd_iu = self.createIU(
                            part["phrase"], "dialogue", RemdisUpdateType.ADD
                        )
                        self.printIU(snd_iu)
                        self.publish(snd_iu, "dialogue")
                        self.output_iu_buffer.append(snd_iu)
                        conc_response += part["phrase"]

            # 対話コンテキストにユーザ発話を追加
            if selected_llm.user_utterance:
                self.history_management("user", selected_llm.user_utterance)
            else:
                self.history_management("user", "(沈黙)")
            self.history_management(
                "assistant",
                self.output_format.format_map(
                    {
                        "style": style,
                        "response": conc_response,
                        "expression": expression,
                        "action": action,
                    }
                ),
            )

        # 応答生成終了メッセージ
        sys.stderr.write(
            "End of selected llm response. Waiting next user uttenrance.\n"
        )
        snd_iu = self.createIU("", "dialogue", RemdisUpdateType.COMMIT)
        self.printIU(snd_iu)
        self.publish(snd_iu, "dialogue")

    # バックチャネルを送信
    def send_backchannel(self):
        iu = self.bc_iu_buffer.get()

        # 現在の状態がidleの場合のみ後続の処理を実行してバックチャネルを送信
        if self.state != "idle":
            return

        # 相槌の送信
        snd_iu = self.createIU(iu["body"]["bc"], "dialogue", RemdisUpdateType.ADD)
        self.printIU(snd_iu)
        self.publish(snd_iu, "dialogue")

    # 応答を中断
    def stop_response(self):
        for iu in self.output_iu_buffer:
            iu["update_type"] = RemdisUpdateType.REVOKE
            self.printIU(iu)
            self.publish(iu, iu["exchange"])
        self.output_iu_buffer = []

    # 音声認識結果受信用のコールバック
    def callback_asr(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.input_iu_buffer.put(in_msg)

    # 動画像処理結果受信用のコールバック
    def callback_video_process(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.input_iu_video_buffer.put(in_msg)

    # 音声合成結果受信用のコールバック
    def callback_tts(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        if in_msg["update_type"] == RemdisUpdateType.COMMIT:
            self.output_iu_buffer = []
            self.system_utterance_end_time = in_msg["timestamp"]
            self.event_queue.put("TTS_COMMIT")

    # VAP情報受信用のコールバック
    def callback_vap(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.event_queue.put(in_msg["body"])

    # バックチャネル受信用のコールバック
    def callback_bc(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.bc_iu_buffer.put(in_msg)
        self.event_queue.put("SYSTEM_BACKCHANNEL")

    # 表情・行動情報受信用のコールバック
    def callback_emo_act(self, ch, method, properties, in_msg):
        in_msg = self.parse_msg(in_msg)
        self.emo_act_iu_buffer.put(in_msg)

    # 対話履歴を更新
    def history_management(self, role, utt):
        self.dialogue_history.append({"role": role, "content": utt})
        if len(self.dialogue_history) > self.history_length:
            self.dialogue_history.pop(0)

    # デバッグ用にログを出力
    def log(self, *args, **kwargs):
        print(f"[{time.time():.5f}]", *args, flush=True, **kwargs)


def main():
    dialogue = Dialogue()
    dialogue.run()


if __name__ == "__main__":
    main()
