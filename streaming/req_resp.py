from common.data.source_model import SourceModel
from streaming.streaming_model import StreamingModel


class StartStreamingRequestEvent(SourceModel):
    def __init__(self):
        super().__init__()

    def map_from_super(self, source_model: SourceModel):
        self.__dict__.update(source_model.__dict__)
        return self


class StartStreamingResponseEvent(StreamingModel):
    def __init__(self):
        super().__init__()

    def map_from_super(self, streaming_model: StreamingModel):
        self.__dict__.update(streaming_model.__dict__)
        return self


class StopStreamingRequestEvent:
    def __init__(self):
        self.id: str = ''


class StopStreamingResponse(StopStreamingRequestEvent):
    def __init__(self):
        super().__init__()
