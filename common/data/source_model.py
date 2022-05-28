from enum import IntEnum

from common.utilities import datetime_now


class RmtpServerType(IntEnum):
    SRS = 0
    SRS_REALTIME = 1
    LIVEGO = 2
    NODE_MEDIA_SERVER = 3


class RtspTransport(IntEnum):
    Auto = 0
    TCP = 1
    UDP = 2
    HTTP = 3

    @staticmethod
    def str(value) -> str:
        if value == RtspTransport.TCP:
            return 'tcp'
        elif value == RtspTransport.UDP:
            return 'udp'
        elif value == RtspTransport.HTTP:
            return 'http'
        else:
            return ''


class AccelerationEngine(IntEnum):
    Auto = 0
    Vdpau = 1
    Cuda = 2
    Vaapi = 3
    Drm = 4
    Opencl = 5
    Cuvid = 6

    @staticmethod
    def create_dict():
        return {
            AccelerationEngine.Auto: 'auto',
            AccelerationEngine.Vdpau: 'vdpau',
            AccelerationEngine.Cuda: 'cuda',
            AccelerationEngine.Vaapi: 'vaapi',
            AccelerationEngine.Drm: 'drm',
            AccelerationEngine.Opencl: 'opencl',
            AccelerationEngine.Cuvid: 'cuvid'
        }

    @staticmethod
    def str(value) -> str:
        return AccelerationEngine.create_dict()[value]


class VideoDecoder(IntEnum):
    Auto = 0
    H264_CUVID = 1
    HEVC_CUVID = 2
    MJPEG_CUVID = 3
    MPEG4_CUVID = 4
    H264_QSV = 5
    HEVC_QSV = 6
    MPEG2_QSV = 7
    H264_MMAL = 8
    MPEG2_MMAL = 9
    MPEG4_MMAL = 10

    @staticmethod
    def create_dict():
        return {
            VideoDecoder.H264_CUVID: 'h264_cuvid',
            VideoDecoder.HEVC_CUVID: 'hevc_cuvid',
            VideoDecoder.MJPEG_CUVID: 'mjpeg_cuvid',
            VideoDecoder.MPEG4_CUVID: 'mpeg4_cuvid',
            VideoDecoder.H264_QSV: 'h264_qsv',
            VideoDecoder.HEVC_QSV: 'hevc_qsvC',
            VideoDecoder.MPEG2_QSV: 'mpeg2_qsvC',
            VideoDecoder.H264_MMAL: 'h264_mmal',
            VideoDecoder.MPEG2_MMAL: 'mpeg2_mmal',
            VideoDecoder.MPEG4_MMAL: 'mpeg4_mmal'
        }

    @staticmethod
    def str(value) -> str:
        return VideoDecoder.create_dict()[value]


class StreamVideoCodec(IntEnum):
    Auto = 0
    libx264 = 1
    libx265 = 2
    copy = 3
    H264_VAAPI = 4
    HEVC_VAAPI = 5
    H264_NVENC = 6
    HEVC_NVENC = 7
    H264_QSV = 8
    HEVC_QSV = 9
    MPEG2_QSV = 10
    H264_OMX = 11
    AV1 = 12
    VP8 = 13
    VP9 = 14

    @staticmethod
    def create_dict():
        return {
            StreamVideoCodec.libx264: 'libx264',
            StreamVideoCodec.libx265: 'libx265',
            StreamVideoCodec.copy: 'copy',
            StreamVideoCodec.H264_VAAPI: 'h264_vaapi',
            StreamVideoCodec.HEVC_VAAPI: 'hevc_vaapi',
            StreamVideoCodec.H264_NVENC: 'h264_nvenc',
            StreamVideoCodec.HEVC_NVENC: 'hevc_nvenc',
            StreamVideoCodec.H264_QSV: 'h264_qsv',
            StreamVideoCodec.HEVC_QSV: 'hevc_qsv',
            StreamVideoCodec.MPEG2_QSV: 'mpeg2_qsv',
            StreamVideoCodec.H264_OMX: 'h264_omx',
            StreamVideoCodec.AV1: 'libaom-av1',
            StreamVideoCodec.VP8: 'libvpx',
            StreamVideoCodec.VP9: 'libvpx-vp9'
        }

    @staticmethod
    def str(value) -> str:
        return StreamVideoCodec.create_dict()[value]


class Preset(IntEnum):
    Auto = 0
    Ultrafast = 1
    Superfast = 2
    Veryfast = 3
    Faster = 4
    Fast = 5
    Medium = 6
    Slow = 7
    Slower = 8
    Veryslow = 9
    Placebo = 10

    @staticmethod
    def create_dict():
        return {
            Preset.Ultrafast: 'ultrafast',
            Preset.Superfast: 'superfast',
            Preset.Veryfast: 'veryfast',
            Preset.Faster: 'faster',
            Preset.Fast: 'fast',
            Preset.Medium: 'medium',
            Preset.Slow: 'slow',
            Preset.Slower: 'slower',
            Preset.Veryslow: 'veryslow',
            Preset.Placebo: 'placebo'
        }

    @staticmethod
    def str(value) -> str:
        return Preset.create_dict()[value]


class Rotate(IntEnum):
    No = 0
    Rotate180 = 1
    Rotate90CounterClockwise = 2
    Rotate90Clockwise = 3
    Rotate90ClockwiseVertical = 4
    Rotate90Counter = 5

    @staticmethod
    def create_dict():
        return {
            Rotate.Rotate180: 'transpose=2,transpose=2',
            Rotate.Rotate90CounterClockwise: 'transpose=0',
            Rotate.Rotate90Clockwise: 'transpose=1',
            Rotate.Rotate90ClockwiseVertical: 'transpose=2',
            Rotate.Rotate90Counter: 'transpose=3'
        }

    @staticmethod
    def str(value) -> str:
        return Rotate.create_dict()[value]


class StreamType(IntEnum):
    FLV = 0
    HLS = 1
    DIRECT_READER = 2
    FFMPEG_READER = 3


class AudioCodec(IntEnum):
    NoAudio = 0
    VORBIS = 1
    OPUS = 2
    MP3LAME = 3
    AAC = 4
    AC3 = 5
    DTS = 6
    ALAC = 7
    copy = 8

    @staticmethod
    def create_dict():
        return {
            AudioCodec.VORBIS: 'libvorbis',
            AudioCodec.OPUS: 'libopus',
            AudioCodec.MP3LAME: 'libmp3lame',
            AudioCodec.AAC: 'aac',
            AudioCodec.AC3: 'ac3',
            AudioCodec.DTS: 'dca',
            AudioCodec.ALAC: 'alac',
            AudioCodec.copy: 'copy'
        }

    @staticmethod
    def str(value) -> str:
        return AudioCodec.create_dict()[value]


class AudioChannel(IntEnum):
    SOURCE = 0
    MONO = 1
    STEREO = 2
    FIVE_DOT_ONE = 3

    @staticmethod
    def create_dict():
        return {
            AudioChannel.MONO: '1',
            AudioChannel.STEREO: '2',
            AudioChannel.FIVE_DOT_ONE: '6'
        }

    @staticmethod
    def str(value) -> str:
        return AudioChannel.create_dict()[value]


class AudioQuality(IntEnum):
    Auto = 0
    BR_400 = 1
    BR_320 = 2
    BR_256 = 3
    BR_224 = 4
    BR_192 = 5
    BR_160 = 6
    BR_128 = 7
    BR_96 = 8
    MUTE = 9

    @staticmethod
    def create_dict():
        return {
            AudioQuality.BR_400: '400k',
            AudioQuality.BR_320: '320k',
            AudioQuality.BR_256: '256k',
            AudioQuality.BR_224: '224k',
            AudioQuality.BR_192: '192k',
            AudioQuality.BR_160: '160k',
            AudioQuality.BR_128: '128k',
            AudioQuality.BR_96: '96k',
            AudioQuality.MUTE: 'mute'
        }

    @staticmethod
    def str(value) -> str:
        return AudioQuality.create_dict()[value]


class AudioSampleRate(IntEnum):
    Auto = 0
    SR_735 = 1
    SR_8 = 2
    SR_11025 = 3
    SR_12 = 4
    SR_16 = 5
    SR_2205 = 6
    SR_24 = 7
    SR_32 = 8
    SR_441 = 9
    SR_48 = 10

    @staticmethod
    def create_dict():
        return {
            AudioSampleRate.SR_735: '7350',
            AudioSampleRate.SR_8: '8000',
            AudioSampleRate.SR_11025: '11025',
            AudioSampleRate.SR_12: '12000',
            AudioSampleRate.SR_16: '16000',
            AudioSampleRate.SR_2205: '22050',
            AudioSampleRate.SR_24: '24000',
            AudioSampleRate.SR_32: '32000',
            AudioSampleRate.SR_441: '44100',
            AudioSampleRate.SR_48: '48000'
        }

    @staticmethod
    def str(value):
        return AudioSampleRate.create_dict()[value]


class RecordFileTypes(IntEnum):
    MP4 = 0
    WEBM = 1
    FLV = 2
    MKV = 3
    AVI = 4
    MPG = 5
    OGV = 6

    @staticmethod
    def create_dict():
        return {
            RecordFileTypes.MP4: 'mp4',
            RecordFileTypes.WEBM: 'webm',
            RecordFileTypes.FLV: 'flv',
            RecordFileTypes.MKV: 'mkv',
            RecordFileTypes.AVI: 'avi',
            RecordFileTypes.MPG: 'mpg',
            RecordFileTypes.OGV: 'ogv'
        }

    @staticmethod
    def str(value) -> str:
        return RecordFileTypes.create_dict()[value]


class RecordVideoCodec(IntEnum):
    Auto = 0
    LIBVPX = 1
    LIBVPX_VP9 = 2
    LIBX265 = 3
    LIBX264 = 4
    copy = 5
    H264_VAAPI = 6
    H265_VAAPI = 7
    H264_NVENC = 8
    HEVC_NVENC = 9
    H264_QSV = 10
    HEVC_QSV = 11
    MPEG2_QSV = 12
    H264_OMX = 13
    VP8_CUVID = 14
    VP9_CUVID = 15
    VP8_QSV = 16

    @staticmethod
    def create_dict():
        return {
            RecordVideoCodec.LIBVPX: 'libvpx',
            RecordVideoCodec.LIBVPX_VP9: 'libvpx-vp9',
            RecordVideoCodec.LIBX265: 'libx265',
            RecordVideoCodec.LIBX264: 'libx264',
            RecordVideoCodec.copy: 'copy',
            RecordVideoCodec.H264_VAAPI: 'h264_vaapi',
            RecordVideoCodec.H265_VAAPI: 'hevc_vaapi',
            RecordVideoCodec.H264_NVENC: 'h264_nvenc',
            RecordVideoCodec.HEVC_NVENC: 'hevc_nvenc',
            RecordVideoCodec.H264_QSV: 'h264_qsv',
            RecordVideoCodec.HEVC_QSV: 'hevc_qsv',
            RecordVideoCodec.MPEG2_QSV: 'mpeg2_qsv',
            RecordVideoCodec.H264_OMX: 'h264_omx',
            RecordVideoCodec.VP8_CUVID: 'vp8_cuvid',
            RecordVideoCodec.VP9_CUVID: 'vp9_cuvid',
            RecordVideoCodec.VP8_QSV: 'vp8_qsv'
        }

    @staticmethod
    def str(value) -> str:
        return RecordVideoCodec.create_dict()[value]


class LogLevel(IntEnum):
    none = 0
    Quiet = 1
    Panic = 2
    Fatal = 3
    Error = 4
    Warning = 5
    Info = 6
    Verbose = 7
    Debug = 8
    Trace = 9

    @staticmethod
    def create_dict():
        return {
            LogLevel.Quiet: 'quiet',
            LogLevel.Panic: 'panic',
            LogLevel.Fatal: 'fatal',
            LogLevel.Error: 'error',
            LogLevel.Warning: 'warning',
            LogLevel.Info: 'info',
            LogLevel.Verbose: 'verbose',
            LogLevel.Debug: 'debug',
            LogLevel.Trace: 'trace'
        }

    @staticmethod
    def str(value) -> str:
        return LogLevel.create_dict()[value]


class FFmpegModel:
    def __init__(self, identifier: str = '', address: str = ''):
        self.id: str = identifier
        self.address: str = address
        self.rtsp_transport: RtspTransport = RtspTransport.Auto

        self.analyzation_duration: int = 1000000
        self.probe_size: int = 1000000
        self.input_frame_rate: int = 0
        self.use_camera_timestamp: bool = False
        self.use_hwaccel: bool = True
        self.hwaccel_engine: AccelerationEngine = AccelerationEngine.Auto
        self.video_decoder: VideoDecoder = VideoDecoder.Auto
        self.hwaccel_device = ''

        self.stream_type: StreamType = StreamType.FLV
        self.rtmp_address: str = ''  # this one is meant to be set from stream model.
        self.stream_video_codec: StreamVideoCodec = StreamVideoCodec.copy
        self.hls_time: int = 2
        self.hls_list_size: int = 3
        self.preset: Preset = Preset.Auto
        self.stream_quality: int = 0
        self.stream_frame_rate: int = 0
        self.stream_width: int = 0
        self.stream_height: int = 0
        self.stream_rotate: Rotate = Rotate.No
        self.stream_audio_codec: AudioCodec = AudioCodec.copy
        self.stream_audio_channel: AudioChannel = AudioChannel.SOURCE
        self.stream_audio_quality: AudioQuality = AudioQuality.Auto
        self.stream_audio_sample_rate: AudioSampleRate = AudioSampleRate.Auto
        self.stream_audio_volume: int = 100

        self.record_file_type: RecordFileTypes = RecordFileTypes.MP4
        self.record_video_codec: RecordVideoCodec = RecordVideoCodec.copy
        self.record_quality: int = 0
        self.record_preset: Preset = Preset.Auto
        self.record_frame_rate: int = 0
        self.record_width: int = 0
        self.record_height: int = 0
        self.record_segment_interval: int = 15
        self.record_rotate: Rotate = Rotate.No
        self.record_audio_codec: AudioCodec = AudioCodec.copy
        self.record_audio_channel: AudioChannel = AudioChannel.SOURCE
        self.record_audio_quality: AudioQuality = AudioQuality.Auto
        self.record_audio_sample_rate: AudioSampleRate = AudioSampleRate.Auto
        self.record_audio_volume: int = 100

        self.log_level: LogLevel = LogLevel.Warning


class SourceModel(FFmpegModel):
    def __init__(self, identifier: str = '', brand: str = '', name: str = '', address: str = ''):
        super().__init__(identifier, address)
        self.brand: str = brand
        self.name: str = name
        self.description: str = ''

        self.enabled: bool = True  # reserved for future using
        self.rtmp_server_type: RmtpServerType = RmtpServerType.LIVEGO  # this one is not used by the command builder but StartStreamEventHandler

        self.snapshot_enabled: bool = False
        self.snapshot_frame_rate: int = 1
        self.snapshot_width: int = 640
        self.snapshot_height: int = 360

        self.ffmpeg_reader_frame_rate: int = 1
        self.ffmpeg_reader_width: int = 640
        self.ffmpeg_reader_height: int = 360

        self.record_enabled: bool = False
        self.ai_clip_enabled: bool = False

        self.created_at: str = datetime_now()

    def get_id(self):
        return self.id

    def get_brand(self):
        return self.brand

    def get_name(self):
        return self.name

    def get_address(self):
        return self.address
