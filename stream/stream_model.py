from command_builder import get_hls_output_path, get_record_output_folder_path
from common.data.source_model import RmtpServerType, SourceModel, StreamType
from common.utilities import datetime_now


class StreamModel:
    def __init__(self):
        # id is used to prevent invalid stream folder name.
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.address: str = ''

        self.rtmp_feeder_pid: int = 0
        self.rtmp_feeder_args: str = ''
        self.hls_pid: int = 0
        self.hls_args: str = ''
        self.created_at: str = datetime_now()

        # extended
        self.stream_type: StreamType = StreamType.FLV
        self.rtmp_server_initialized: bool = False
        self.rtmp_server_type: RmtpServerType = RmtpServerType.LIVEGO
        self.rtmp_image_name: str = ''
        self.rtmp_container_name: str = ''
        self.rtmp_address: str = ''
        self.rtmp_flv_address: str = ''
        self.rtmp_container_ports: str = ''
        self.rtmp_container_commands: str = ''

        self.ffmpeg_reader_pid: int = 0
        self.ffmpeg_reader_frame_rate: int = 1
        self.ffmpeg_reader_width: int = 640
        self.ffmpeg_reader_height: int = 360

        self.record_enabled: bool = False
        self.record_pid: int = 0
        self.record_args: str = ''
        self.record_duration: int = 15

        # FFmpeg snapshot for AI.
        self.snapshot_enabled: bool = False
        self.snapshot_pid: int = 0
        self.snapshot_frame_rate: int = 1
        self.snapshot_width: int = 640
        self.snapshot_height: int = 360

        self.video_clip_enabled: bool = False

        # paths
        self.hls_output_path: str = ''
        self.record_output_folder_path: str = ''

    def set_paths(self):
        self.hls_output_path = get_hls_output_path(self.id)
        self.record_output_folder_path = get_record_output_folder_path(self.id)

    def map_from_source(self, source: SourceModel):
        # noinspection DuplicatedCode
        self.id = source.id
        self.brand = source.brand
        self.name = source.name
        self.address = source.address

        self.stream_type = source.stream_type
        self.rtmp_server_type = source.rtmp_server_type

        # noinspection DuplicatedCode
        self.ffmpeg_reader_frame_rate = source.ffmpeg_reader_frame_rate
        self.ffmpeg_reader_width = source.ffmpeg_reader_width
        self.ffmpeg_reader_height = source.ffmpeg_reader_height

        self.snapshot_enabled = source.snapshot_enabled
        self.snapshot_frame_rate: source.snapshot_frame_rate
        self.snapshot_width: int = source.snapshot_width
        self.snapshot_height: int = source.snapshot_height

        self.record_enabled = source.record_enabled
        self.record_duration = source.record_segment_interval

        self.video_clip_enabled = source.video_clip_enabled

        self.set_paths()

        return self

    def is_hls_enabled(self) -> bool:
        return self.stream_type == StreamType.HLS

    def is_record_enabled(self) -> bool:
        return self.record_enabled

    def is_snapshot_enabled(self) -> bool:
        return self.snapshot_enabled

    def is_ffmpeg_reader_enabled(self) -> bool:
        return self.stream_type == StreamType.FFMPEG_READER
