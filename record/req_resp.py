class VideoFileMergerRequestEvent:
    def __init__(self):
        self.id: str = ''
        self.date_str: str = ''


class VideoFileMergerResponseEvent:
    id: str = ''
    result: bool = False
