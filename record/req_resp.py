from typing import List


class ProbeResult:
    source_id: str = ''
    video_filename: str = ''
    date_str: str = ''
    duration: int = 0


class VfiResponseEvent:
    results: List[ProbeResult] = []


class VideoFileMergerRequestEvent:
    def __init__(self):
        self.id: str = ''
        self.date_str: str = ''


class VideoFileMergerResponseEvent:
    id: str = ''
    result: bool = False
