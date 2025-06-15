import asyncio
import json
import threading

from base import RemdisModule
from websockets.asyncio.server import ServerConnection, serve


class TravelViewer(RemdisModule):
    def __init__(self, pub_exchanges=[], sub_exchanges=["dialogue3"]):
        super().__init__(pub_exchanges=pub_exchanges, sub_exchanges=sub_exchanges)
        self._is_running = True
        self.host = self.config["TRAVEL_VIEWER"]["server_host"]
        self.port = self.config["TRAVEL_VIEWER"]["server_port"]
        self.loop = None

        self.output_buffer = asyncio.Queue()

    def run(self):
        self.loop = asyncio.get_event_loop()

        # メッセージ受信スレッド
        t1 = threading.Thread(target=self.listen_loop)

        # スレッド実行
        t1.start()

        # 送信サーバー
        self.loop.run_until_complete(self.run_viewer_server())

        t1.join()

    def listen_loop(self):
        self.subscribe("dialogue3", self.on_dialogue3_event)

    def on_dialogue3_event(self, ch, method, properties, in_msg):
        parsed_msg = self.parse_msg(in_msg)
        self.printIU(parsed_msg)
        self.loop.call_soon_threadsafe(
            self.output_buffer.put_nowait, parsed_msg["body"]
        )

    async def callback(self, websocket: ServerConnection):
        print("[Travel Viewer] Connected to a client.")
        while True:
            data = await self.output_buffer.get()
            await websocket.send(json.dumps(data))
            await asyncio.sleep(0.5)

    async def run_viewer_server(self):
        async with serve(self.callback, self.host, self.port):
            await asyncio.get_running_loop().create_future()


def main():
    viewer = TravelViewer()
    viewer.run()


if __name__ == "__main__":
    main()
