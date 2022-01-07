from typing import Dict


class StreamingModel:
    def __init__(self):
        self.name: str = ''
        self.id: str = ''
        self.rtsp_address: str = ''
        self.brand: str = ''
        self.output_file: str = ''
        self.pid: int = -1
        self.created_at: str = ''
        self.args: str = ''

    def map_from(self, dic: Dict):
        self.id = dic['id'] if 'id' in dic else ''
        self.pid = dic['pid'] if 'pid' in dic else -1
        self.name = dic['name'] if 'name' in dic else ''
        self.args = dic['args'] if 'args' in dic else ''
        self.created_at = dic['created_at'] if 'created_at' in dic else ''
        self.rtsp_address = dic['rtsp_address'] if 'rtsp_address' in dic else ''
        self.brand = dic['brand'] if 'brand' in dic else ''
        self.output_file = dic['output_file'] if 'output_file' in dic else ''
        return self
