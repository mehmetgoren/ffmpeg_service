from typing import List


class ProbeResult:
    source_id: str = ''
    video_filename: str = ''
    date_str: str = ''
    duration: int = 0


class VfiResponseEvent:
    results: List[ProbeResult] = []


class VfmRequestEvent:
    def __init__(self):
        self.source_id: str = ''
        self.date_str: str = ''


class VfmResponseEvent:
    source_id: str = ''
    output_file_name: str = ''
    merged_video_filenames: List[str] = []
    merged_video_file_duration: int = 0
