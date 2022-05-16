import os

from stream.stream_model import StreamModel, RecordFileTypes
from utils.dir import get_record_dir_by, get_sorted_valid_files


class RecStuckModel:
    def __init__(self):
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.address: str = ''
        self.record_segment_interval: int = 0
        self.record_output_dir: str = ''
        self.file_ext: str = ''

        self.last_modified_file: str = ''
        self.last_modified_size: int = 0

        self.failed_count: int = 0
        self.failed_modified_file: str = ''

        self.last_check_at: str = ''

    def from_stream(self, stream_model: StreamModel):
        self.id = stream_model.id
        self.brand = stream_model.brand
        self.name = stream_model.name
        self.address = stream_model.address
        self.record_segment_interval = stream_model.record_segment_interval
        self.record_output_dir = get_record_dir_by(stream_model.id)
        self.file_ext = '.' + RecordFileTypes.str(stream_model.record_file_type)

        first_file = ''
        files = get_sorted_valid_files(self.record_output_dir, self.file_ext)
        if len(files) > 0:
            first_file = files[0]

        self.last_modified_file = first_file
        self.last_modified_size = os.path.getsize(self.last_modified_file)

        return self
