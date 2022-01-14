from typing import Dict


class StreamingModel:
    def __init__(self):
        self.name: str = ''
        # id is used to prevent invalid streaming folder name. The real identifier is presented by 'name' field.
        self.id: str = ''
        self.rtsp_address: str = ''
        self.brand: str = ''
        self.output_file: str = ''
        self.pid: int = -1
        self.created_at: str = ''
        self.args: str = ''
        self.failed_count: int = 0

    def map_from(self, dic: Dict):
        self.id = dic['id'] if 'id' in dic else ''
        self.pid = int(dic['pid']) if 'pid' in dic else -1
        self.name = dic['name'] if 'name' in dic else ''
        self.args = dic['args'] if 'args' in dic else ''
        self.created_at = dic['created_at'] if 'created_at' in dic else ''
        self.rtsp_address = dic['rtsp_address'] if 'rtsp_address' in dic else ''
        self.brand = dic['brand'] if 'brand' in dic else ''
        self.output_file = dic['output_file'] if 'output_file' in dic else ''
        self.failed_count = int(dic['failed_count']) if 'failed_count' in dic else 0
        return self


class RecordingModel(StreamingModel):
    def __init__(self):
        super().__init__()
        # todo: move to config later
        self.duration: int = 3

    def map_from(self, dic: Dict):
        super().map_from(dic)
        self.duration = int(dic['duration']) if 'duration' in dic else 15
        return self
