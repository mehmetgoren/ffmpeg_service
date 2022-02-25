from common.data.source_model import SourceModel


class FailedStreamModel:
    def __init__(self):
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.rtsp_address: str = ''

        self.watch_dog_interval: float = .0

        self.stream_failed_count: int = 0
        self.record_failed_count: int = 0
        self.reader_failed_count: int = 0
        self.record_stuck_failed_count: int = 0

    def map_from_source(self, source: SourceModel):
        self.id = source.id
        self.brand = source.brand
        self.name = source.name
        self.rtsp_address = source.rtsp_address
        return self
