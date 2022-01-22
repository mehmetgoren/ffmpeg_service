from enum import IntEnum


class InputType(IntEnum):
    H264 = 0
    MPEG4 = 1
    HLS = 2


class RtspTransport(IntEnum):
    Auto = 0
    TCP = 1
    UDP = 2
    HTTP = 3

    def __str__(self):
        if self == RtspTransport.TCP:
            return 'tcp'
        elif self == RtspTransport.UDP:
            return 'udp'
        elif self == RtspTransport.HTTP:
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

    def __str__(self):
        return AccelerationEngine.create_dict()[self]


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

    def __str__(self):
        return VideoDecoder.create_dict()[self]


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
            StreamVideoCodec.H264_OMX: 'h264_omx'
        }

    def __str__(self):
        return StreamVideoCodec.create_dict()[self]


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

    def __str__(self):
        return Preset.create_dict()[self]


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

    def __str__(self):
        return Rotate.create_dict()[self]


class StreamType(IntEnum):
    HLS = 0
    MP4 = 1
    HEVC_H265 = 2


class AudioCodec(IntEnum):
    Auto = 0
    NoAudio = 1
    LIBVORBIS = 2
    LIBOPUS = 3
    LIBMP3LAME = 4
    AAC = 5
    AC3 = 6
    copy = 7

    @staticmethod
    def create_dict():
        return {
            AudioCodec.LIBVORBIS: 'libvorbis',
            AudioCodec.LIBOPUS: 'libopus',
            AudioCodec.LIBMP3LAME: 'libmp3lame',
            AudioCodec.AAC: 'aac',
            AudioCodec.AC3: 'ac3',
            AudioCodec.copy: 'copy'
        }

    def __str__(self):
        return AudioCodec.create_dict()[self]


class LogLevel(IntEnum):
    Info = 0
    Silent = 1
    Warning = 2
    Error = 3
    Fatal = 4

    @staticmethod
    def create_dict():
        return {
            LogLevel.Silent: 'quiet',
            LogLevel.Warning: 'warning',
            LogLevel.Error: 'error',
            LogLevel.Fatal: 'fatal'
        }

    def __str__(self):
        return LogLevel.create_dict()[self]


class SourceSettings:
    def __init__(self):
        self.id: str = ''
        self.name: str = ''
        self.brand: str = ''
        self.rtsp_address: str = ''
        self.description: str = ''
        self.output_file: str = ''
        self.enabled: bool = True
        self.recording: bool = False
        self.input_type: InputType = InputType.H264
        self.rtsp_transport: RtspTransport = RtspTransport.TCP
        self.analyzation_duration: int = 1000000
        self.probe_size: int = 1000000
        self.fps: int = 0
        self.use_camera_timestamp: bool = False
        self.use_hwaccel: bool = True
        self.hwaccel_engine: AccelerationEngine = AccelerationEngine.Auto
        self.video_decoder: VideoDecoder = VideoDecoder.Auto
        self.hwaccel_device = ''
        self.stream_type: StreamType = StreamType.HLS
        self.stream_video_codec: StreamVideoCodec = StreamVideoCodec.copy
        self.hls_time: int = 2
        self.hls_list_size: int = 3
        self.hls_preset: Preset = Preset.Superfast
        self.stream_quality: int = 0
        self.stream_width: int = 0
        self.stream_height: int = 0
        self.stream_rotate: Rotate = Rotate.No
        self.stream_video_filter: str = ''
        self.stream_audio_codec: AudioCodec = AudioCodec.NoAudio

        self.log_level: LogLevel = LogLevel.Warning
