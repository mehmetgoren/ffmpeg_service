from common.data.source_model import SourceModel
from stream.stream_model import StreamModel


class StartStreamRequestEvent(SourceModel):
    def __init__(self):
        super().__init__()


class StartStreamResponseEvent(StreamModel):
    def __init__(self):
        super().__init__()


class StopStreamRequestEvent:
    def __init__(self):
        self.id: str = ''


class StopStreamResponse(StopStreamRequestEvent):
    def __init__(self):
        super().__init__()
