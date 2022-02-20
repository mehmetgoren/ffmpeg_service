from command_builder import get_hls_output_path, get_read_jpeg_output_path, get_record_output_folder_path
from common.data.source_model import RmtpServerType, SourceModel, StreamType, FlvPlayerConnectionType
from common.utilities import datetime_now


class StreamModel:
    def __init__(self):
        # id is used to prevent invalid stream folder name.
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.rtsp_address: str = ''

        # stream
        self.pid: int = -1
        self.created_at: str = datetime_now()
        self.args: str = ''

        # extended
        self.stream_type: StreamType = StreamType.HLS
        self.rtmp_server_initialized: bool = False
        self.rtmp_server_type: RmtpServerType = RmtpServerType.SRS
        self.flv_player_connection_type: FlvPlayerConnectionType = FlvPlayerConnectionType.HTTP
        self.need_reload_interval: int = 300  # this one is hls/flv player reload value. Not used in the command builder
        self.rtmp_image_name: str = ''
        self.rtmp_container_name: str = ''
        self.rtmp_address: str = ''
        self.rtmp_flv_address: str = ''
        self.rtmp_container_ports: str = ''
        self.rtmp_container_commands: str = ''

        self.direct_read_frame_rate: int = 1
        self.direct_read_width: int = 640
        self.direct_read_height: int = 360

        self.jpeg_enabled: bool = False
        self.jpeg_frame_rate: int = 0
        self.use_disk_image_reader_service: bool = False

        self.record: bool = False
        self.record_duration: int = 15
        self.record_flv_pid: int = 0
        self.record_flv_args: str = ''
        self.record_flv_failed_count: int = 0

        # paths
        self.hls_output_path: str = ''
        self.read_jpeg_output_path: str = ''
        self.record_output_folder_path: str = ''

    def set_paths(self):
        self.hls_output_path = get_hls_output_path(self.id)
        self.read_jpeg_output_path = get_read_jpeg_output_path(self.id)
        self.record_output_folder_path = get_record_output_folder_path(self.id)

    def map_from_source(self, source: SourceModel):
        # noinspection DuplicatedCode
        self.id = source.id
        self.brand = source.brand
        self.name = source.name
        self.rtsp_address = source.rtsp_address

        self.stream_type = source.stream_type
        self.rtmp_server_type = source.rtmp_server_type
        self.flv_player_connection_type = source.flv_player_connection_type
        self.need_reload_interval = source.need_reload_interval

        # noinspection DuplicatedCode
        self.direct_read_frame_rate = source.direct_read_frame_rate
        self.direct_read_width = source.direct_read_width
        self.direct_read_height = source.direct_read_height

        self.jpeg_enabled = source.jpeg_enabled
        self.jpeg_frame_rate = source.jpeg_frame_rate
        self.use_disk_image_reader_service = source.use_disk_image_reader_service

        self.record = source.record
        self.record_duration = source.record_segment_interval

        self.set_paths()

        return self
