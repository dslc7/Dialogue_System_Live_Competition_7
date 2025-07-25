import re
import time

import openai
from base import MMDAgentEXLabel

STYLES = ["chat", "cheerful", "customerservice"]


class ResponseGenerator:
    def __init__(self, config, asr_timestamp, query, dialogue_history, prompts):
        # 設定の読み込み
        self.max_tokens = config["ChatGPT"]["max_tokens"]
        self.max_message_num_in_context = config["ChatGPT"][
            "max_message_num_in_context"
        ]
        self.model = config["ChatGPT"]["response_generation_model"]
        self.is_output_tts_style = (
            True if config["ChatGPT"]["output_tts_style"] == "on" else False
        )

        # 処理対象のユーザ発話に関する情報
        self.asr_timestamp = asr_timestamp
        self.query = query
        self.dialogue_history = dialogue_history
        self.prompts = prompts

        # 生成中の応答を保持・パースする変数
        self.outputting_tts_style = (
            True if config["ChatGPT"]["output_tts_style"] == "on" else False
        )
        self.response_fragment = ""
        self.response_fragment_tts = ""
        self.punctuation_pattern = re.compile("[、。！？]")

        # ChatGPTに入力する対話文脈
        messages = []

        # 対話履歴の構築
        if "SYSTEM" in self.prompts and self.prompts["SYSTEM"]:
            messages.append({"role": "system", "content": self.prompts["SYSTEM"]})
        messages.append({"role": "user", "content": self.prompts["RESP"]})
        i = max(0, len(self.dialogue_history) - self.max_message_num_in_context)
        if self.dialogue_history and self.dialogue_history[i]["role"] == "user":
            # Merge into the first prompt
            messages[-1]["content"] += f"\n\n以下の発話への返答から始めてください:\n{self.dialogue_history[i]['content']}"
            i += 1
        messages.extend(self.dialogue_history[i:])
        messages.append({"role": "user", "content": query if query else self.prompts["TO"]})
        self.log(f"Call ChatGPT: {query=}")

        # ChatGPTに対話文脈を入力してストリーミング形式で応答の生成を開始
        self.response = openai.ChatCompletion.create(
            model=self.model, messages=messages, max_tokens=self.max_tokens, stream=True
        )

    # Dialogueのsend_response関数で呼び出され，応答の断片を順次返す
    def __next__(self):
        # ChatGPTの応答を順次パースして返す
        for chunk in self.response:
            chunk_message = chunk["choices"][0]["delta"]
            new_token = chunk_message.get("content", "")
            if self.is_output_tts_style and self.outputting_tts_style:
                # 応答の断片を追加
                if new_token != "/":
                    self.response_fragment += new_token

                # 応答の最後が来た場合は残りの断片を返す
                if new_token == "/":
                    for style in STYLES:
                        if style in self.response_fragment:
                            self.outputting_tts_style = False
                            self.response_fragment = ""
                            return {"tts_style": style}
                    else:
                        print(
                            "\033[33mLLM didn't output `tts_style`, so it will output `chat`\033[0m"
                        )
                        self.outputting_tts_style = False
                        return {"tts_style": "chat"}

            else:
                new_token = chunk_message.get("content", "")

                # 応答の断片を追加
                if new_token != "/":
                    self.response_fragment += new_token

                # 句読点で応答を分割
                splits = self.punctuation_pattern.split(self.response_fragment, 1)

                # 次のループのために残りの断片を保持
                self.response_fragment = splits[-1]

                # 句読点が存在していた場合は1つ目の断片を返す
                if len(splits) == 2 or new_token == "/":
                    if splits[0]:
                        return {"phrase": splits[0]}

                # 応答の最後が来た場合は残りの断片を返す
                if new_token == "/":
                    if self.response_fragment:
                        self.outputting_tts_style = True
                        phrase = self.response_fragment
                        self.response_fragment = ""
                        return {"phrase": phrase}
        # ChatGPTの応答が完了した場合は残りの断片をパースして返す
        if self.response_fragment:
            self.outputting_tts_style = True
            phrase = self.response_fragment
            self.response_fragment = ""
            if self._is_exp_format(phrase):
                return self._parse_split(phrase)
            return {"phrase": phrase}

        raise StopIteration

    # 引数（例: '1_喜び,6_会釈'）をパースして，expressionとactionを取得
    def _parse_split(self, split: str):
        expression = MMDAgentEXLabel.id2expression[0]
        action = MMDAgentEXLabel.id2action[0]

        # expression/actionを取得
        if "," in split:
            expression, action = split.split(",", 1)

            expression = expression.split("_")[0]
            expression = int(expression) if expression.isdigit() else 0
            expression = MMDAgentEXLabel.id2expression[expression]

            action = action.split("_")[0]
            action = int(action) if action.isdigit() else 0
            action = MMDAgentEXLabel.id2action[action]

        return {"expression": expression, "action": action}

    def _is_exp_format(self, string: str) -> bool:
        exp_act = string.split(",", 1)
        if len(exp_act) != 2:
            return False
        expression, action = exp_act
        if len(expression.split("_")) != 2:
            return False
        if len(action.split("_")) != 2:
            return False
        return True

    # ResponseGeneratorをイテレータ化
    def __iter__(self):
        return self

    # デバッグ用のログ出力
    def log(self, *args, **kwargs):
        print(f"[{time.time():.5f}]", *args, flush=True, **kwargs)


class ResponseChatGPT:
    def __init__(self, config, prompts):
        self.config = config
        self.prompts = prompts

        # 設定の読み込み
        openai.api_key = config["ChatGPT"]["api_key"]

        # 入力されたユーザ発話に関する情報を保持する変数
        self.user_utterance = ""
        self.response = ""
        self.last_asr_iu_id = ""
        self.asr_time = 0.0

    # ChatGPTの呼び出しを開始
    def run(
        self,
        asr_timestamp,
        user_utterance,
        dialogue_history,
        last_asr_iu_id,
        parent_llm_buffer,
    ):
        self.user_utterance = user_utterance
        self.last_asr_iu_id = last_asr_iu_id
        self.asr_time = asr_timestamp

        # ChataGPTを呼び出して応答の生成を開始
        self.response = ResponseGenerator(
            self.config, asr_timestamp, user_utterance, dialogue_history, self.prompts
        )

        # 自身をDialogueモジュールが持つLLMバッファに追加
        parent_llm_buffer.put(self)


if __name__ == "__main__":
    openai.api_key = "<enter your API key>"

    config = {
        "ChatGPT": {
            "max_tokens": 64,
            "max_message_num_in_context": 3,
            "response_generation_model": "gpt-3.5-turbo",
        }
    }

    asr_timestamp = time.time()
    query = "今日は良い天気だね"
    dialogue_history = []
    prompts = {}

    with open("./prompt/response.txt") as f:
        prompts["RESP"] = f.read()

    response_generator = ResponseGenerator(
        config, asr_timestamp, query, dialogue_history, prompts
    )

    for part in response_generator:
        response_generator.log(part)
