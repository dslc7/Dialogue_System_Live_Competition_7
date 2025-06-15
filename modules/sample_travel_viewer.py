import time

from base import RemdisModule, RemdisUpdateType

# Travel Viewer Docs: https://github.com/dslc7/travel-viewer/blob/main/README.md

DATA_1 = [
    {
        "imgUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/%E6%9D%B1%E4%BA%AC%E3%82%BF%E3%83%AF%E3%83%BC_%28214699253%29.jpeg/640px-%E6%9D%B1%E4%BA%AC%E3%82%BF%E3%83%AF%E3%83%BC_%28214699253%29.jpeg",
        "name": "東京タワー",
        "yomigana": "とうきょうたわー",
        "q": "35.65861,139.74556",
    }
]

DATA_2 = [
    {
        "imgUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/%E6%9D%B1%E4%BA%AC%E3%82%BF%E3%83%AF%E3%83%BC_%28214699253%29.jpeg/640px-%E6%9D%B1%E4%BA%AC%E3%82%BF%E3%83%AF%E3%83%BC_%28214699253%29.jpeg",
        "name": "東京タワー",
        "yomigana": "とうきょうたわー",
    },
    {
        "imgUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/%E3%82%B9%E3%82%AB%E3%82%A4%E3%83%84%E3%83%AA%E3%83%BC_-_panoramio_%2820%29.jpg/640px-%E3%82%B9%E3%82%AB%E3%82%A4%E3%83%84%E3%83%AA%E3%83%BC_-_panoramio_%2820%29.jpg",
        "name": "東京スカイツリー",
        "yomigana": "とうきょうすかいつりー",
    },
    {
        "imgUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/%E9%9B%B7%E9%96%80%E3%80%82_-_panoramio.jpg/640px-%E9%9B%B7%E9%96%80%E3%80%82_-_panoramio.jpg",
        "name": "雷門",
        "yomigana": "かみなりもん",
    },
]


class SampleTravelViewer(RemdisModule):
    def __init__(
        self,
        pub_exchanges=["dialogue3"],
        sub_exchanges=[],
    ):
        super().__init__(pub_exchanges=pub_exchanges, sub_exchanges=sub_exchanges)
        self._is_running = True

    def run(self):
        time.sleep(2)
        while True:
            snd_iu = self.createIU(DATA_1, "dialogue3", RemdisUpdateType.ADD)
            self.publish(snd_iu, "dialogue3")
            time.sleep(5)

            snd_iu = self.createIU(DATA_2, "dialogue3", RemdisUpdateType.ADD)
            self.publish(snd_iu, "dialogue3")
            time.sleep(5)


def main():
    test_travel_viewer = SampleTravelViewer()
    test_travel_viewer.run()


if __name__ == "__main__":
    main()
