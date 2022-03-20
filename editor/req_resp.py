from enum import IntEnum


class EditorEventType(IntEnum):
    NONE = 0
    TAKE_SCREENSHOT = 1
    GENERATE_THUMBNAIL = 2


class EditorRequestEvent:
    def __init__(self):
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.address: str = ''
        self.event_type: EditorEventType = EditorEventType.NONE


class EditorResponseEvent(EditorRequestEvent):
    def __init__(self):
        super().__init__()
        self.image_base64: str = ''

    def map_from_super(self, request: EditorRequestEvent):
        self.__dict__.update(request.__dict__)
        return self
