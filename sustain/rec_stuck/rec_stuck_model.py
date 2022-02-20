import glob
import os

from stream.stream_model import StreamModel


class RecStuckModel:
    def __init__(self):
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.rtsp_address: str = ''
        self.record_output_folder_path: str = ''

        self.last_modified_file: str = ''
        self.last_modified_size: int = 0

        self.failed_count: int = 0
        self.failed_modified_file: str = ''

    def from_stream(self, stream_model: StreamModel):
        self.id = stream_model.id
        self.brand = stream_model.brand
        self.name = stream_model.name
        self.rtsp_address = stream_model.rtsp_address
        self.record_output_folder_path = stream_model.record_output_folder_path

        list_of_files = glob.glob(f'{self.record_output_folder_path}/*')  # * means all if it needs specific format then *.csv
        self.last_modified_file = max(list_of_files, key=os.path.getctime)
        self.last_modified_size = os.path.getsize(self.last_modified_file)

        return self
