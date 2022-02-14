from common.data.source_model import SourceModel
from stream.stream_model import StreamModel


class StartStreamRequestEvent(SourceModel):
    def __init__(self):
        super().__init__()

    def map_from_super(self, source_model: SourceModel):
        self.__dict__.update(source_model.__dict__)
        return self


class StartStreamResponseEvent(StreamModel):
    def __init__(self):
        super().__init__()

    def map_from_super(self, stream_model: StreamModel):
        self.__dict__.update(stream_model.__dict__)
        return self


class StopStreamRequestEvent:
    def __init__(self):
        self.id: str = ''


class StopStreamResponse(StopStreamRequestEvent):
    def __init__(self):
        super().__init__()
