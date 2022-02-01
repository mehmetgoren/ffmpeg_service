from command_builder import get_hls_output_path, get_read_jpeg_output_path, get_recording_output_folder_path
from common.data.base_repository import map_from
from common.data.source_model import RmtpServerType, SourceModel, StreamType, FlvPlayerConnectionType


class StreamingModel:
    def __init__(self):
        # id is used to prevent invalid streaming folder name.
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.rtsp_address: str = ''

        self.enabled: bool = False

        # streaming
        self.pid: int = -1
        self.created_at: str = ''
        self.args: str = ''
        self.failed_count: int = 0

        # extended
        self.streaming_type: StreamType = StreamType.HLS
        self.rtmp_server_initialized: bool = False
        self.rtmp_server_type: RmtpServerType = RmtpServerType.SRS
        self.flv_player_connection_type: FlvPlayerConnectionType = FlvPlayerConnectionType.HTTP
        self.rtmp_image_name: str = ''
        self.rtmp_container_name: str = ''
        self.rtmp_address: str = ''
        self.rtmp_flv_address: str = ''
        self.rtmp_container_ports: str = ''
        self.rtmp_container_commands: str = ''

        self.recording: bool = False
        self.record_duration: int = 15

        # paths
        self.hls_output_path: str = ''
        self.read_jpeg_output_path: str = ''
        self.recording_output_folder_path: str = ''

    @staticmethod
    def __set_paths(self):
        self.hls_output_path = get_hls_output_path(self.id)
        self.read_jpeg_output_path = get_read_jpeg_output_path(self.id)
        self.recording_output_folder_path = get_recording_output_folder_path(self.id)

    def map_from(self, fixed_dic: dict):
        typed_dic = map_from(fixed_dic, StreamingModel(), self)
        self.__set_paths(typed_dic)
        return self

    def map_from_source(self, source: SourceModel):
        self.id = source.id
        self.name = source.name
        self.rtsp_address = source.rtsp_address

        self.enabled = source.enabled

        self.streaming_type = source.stream_type
        self.rtmp_server_type = source.rtmp_server_type
        self.flv_player_connection_type = source.flv_player_connection_type

        self.recording = source.recording
        self.record_duration = source.record_segment_interval
        self.__set_paths(self)
        return self
