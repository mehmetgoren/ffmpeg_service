from common.utilities import datetime_now
from stream.stream_model import StreamModel
from sustain.failed_stream.failed_stream_model import WatchDogOperations


class NotifyFailedStreamModel:
    def __init__(self):
        self.failure_reason: str = ''
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.address: str = ''
        self.created_at: str = ''

    def map_from(self, op: WatchDogOperations, stream_model: StreamModel) -> any:
        self.failure_reason = op
        self.id = stream_model.id
        self.brand = stream_model.brand
        self.name = stream_model.name
        self.address = stream_model.address
        self.created_at = datetime_now()
        return self
