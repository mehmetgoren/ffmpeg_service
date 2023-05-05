from common.data.source_model import MediaServerType, SourceModel, StreamType, RecordFileTypes, SnapshotType, FlvPlayerType, Go2RtcPlayerMode
from common.utilities import datetime_now


class StreamModel:
    def __init__(self):
        # id is used to prevent invalid stream folder name.
        self.id: str = ''
        self.brand: str = ''
        self.name: str = ''
        self.address: str = ''

        self.ms_feeder_pid: int = 0  # ms prefix is for media server.
        self.ms_feeder_args: str = ''
        self.hls_pid: int = 0
        self.hls_args: str = ''
        self.created_at: str = datetime_now()

        # extended
        self.ms_type: MediaServerType = MediaServerType.GO_2_RTC
        self.stream_type: StreamType = StreamType.FLV
        self.ms_initialized: bool = False
        self.ms_image_name: str = ''
        self.ms_container_name: str = ''
        self.ms_address: str = ''
        self.ms_stream_address: str = ''  # i.e http://127.0.0.1:7008/live/livestream.flv or http://127.0.0.1:1985/api/ws?src=camera1
        self.ms_container_ports: str = ''
        self.ms_container_commands: str = ''

        self.mp_ffmpeg_reader_owner_pid: int = 0
        self.ffmpeg_reader_frame_rate: int = 1
        self.ffmpeg_reader_width: int = 640
        self.ffmpeg_reader_height: int = 360

        self.record_enabled: bool = False
        self.record_file_type: RecordFileTypes = RecordFileTypes.MP4
        self.record_pid: int = 0
        self.record_args: str = ''
        self.record_segment_interval: int = 15

        # FFmpeg snapshot for AI.
        self.snapshot_enabled: bool = False
        self.snapshot_pid: int = 0
        self.snapshot_type: SnapshotType = SnapshotType.FFmpeg
        self.snapshot_frame_rate: int = 1
        self.snapshot_width: int = 640
        self.snapshot_height: int = 360

        self.ai_clip_enabled: bool = False

        self.concat_demuxer_pid: int = 0
        self.concat_demuxer_args: str = ''

        self.root_dir_path = ''

        self.flv_player_type: FlvPlayerType = FlvPlayerType.MpegTsJs
        self.booster_enabled: bool = False  # this one is used by FLV and HLS player
        self.live_buffer_latency_chasing: bool = True  # this one is used by mpegts player

        self.go2rtc_player_mode = Go2RtcPlayerMode.Mse

    def map_from_source(self, source: SourceModel):
        # noinspection DuplicatedCode
        self.id = source.id
        self.brand = source.brand
        self.name = source.name
        self.address = source.address

        self.ms_type = source.ms_type
        self.stream_type = source.stream_type

        self.ffmpeg_reader_frame_rate = source.ffmpeg_reader_frame_rate
        self.ffmpeg_reader_width = source.ffmpeg_reader_width
        self.ffmpeg_reader_height = source.ffmpeg_reader_height

        self.snapshot_enabled = source.snapshot_enabled
        self.snapshot_type = source.snapshot_type
        self.snapshot_frame_rate: int = source.snapshot_frame_rate
        self.snapshot_width: int = source.snapshot_width
        self.snapshot_height: int = source.snapshot_height

        # noinspection DuplicatedCode
        self.record_enabled = source.record_enabled
        self.record_file_type = source.record_file_type
        self.record_segment_interval = source.record_segment_interval

        self.ai_clip_enabled = source.ai_clip_enabled

        self.root_dir_path = source.root_dir_path

        self.flv_player_type = source.flv_player_type
        self.booster_enabled = source.booster_enabled
        self.live_buffer_latency_chasing = source.live_buffer_latency_chasing

        self.go2rtc_player_mode = source.go2rtc_player_mode

        return self

    def is_hls_enabled(self) -> bool:
        return self.stream_type == StreamType.HLS

    def is_record_enabled(self) -> bool:
        return self.record_enabled

    def is_ffmpeg_snapshot_enabled(self) -> bool:
        return self.snapshot_enabled and self.snapshot_type == SnapshotType.FFmpeg

    def is_opencv_persistent_snapshot_enabled(self) -> bool:
        return self.snapshot_enabled and self.snapshot_type == SnapshotType.OpenCVPersistent

    def is_ai_clip_enabled(self) -> bool:
        return self.snapshot_enabled and self.ai_clip_enabled

    def is_mp_ffmpeg_pipe_reader_enabled(self) -> bool:
        return self.stream_type == StreamType.PIPE_READER
