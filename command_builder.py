import os
from typing import List

from common.data.source_model import FFmpegModel, RtspTransport, VideoDecoder, StreamType, StreamVideoCodec, Preset, Rotate, AudioCodec, \
    LogLevel, AudioChannel, AudioQuality, AudioSampleRate, RecordFileTypes, RecordVideoCodec, AccelerationEngine, MediaServerType
from common.utilities import config
from utils.dir import get_record_dir_by, get_ai_clip_dir, get_hls_path


class CommandBuilder:
    def __init__(self, source_model: FFmpegModel):
        self.ffmpeg_model: FFmpegModel = source_model
        self.use_double_quotes_for_path: bool = config.ffmpeg.use_double_quotes_for_path

    def __add_double_quotes(self, path: str):
        if self.use_double_quotes_for_path:
            path = f'"{path}"'
        return path

    def build_input(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        args: List[str] = ['ffmpeg', '-progress', 'pipe:5']

        if f.use_camera_timestamp:
            args.extend(['-use_wallclock_as_timestamps', '1'])  # cause delay, check it
        if f.input_frame_rate > 0:
            args.extend(['-r', str(f.input_frame_rate)])
        args.extend(['-analyzeduration', str(f.analyzation_duration), '-probesize', str(f.probe_size)])
        args.extend(['-fflags', '+igndts'])
        if f.rtsp_transport != RtspTransport.Auto:
            args.extend(['-rtsp_transport', RtspTransport.str(f.rtsp_transport)])
        if f.use_hwaccel:
            args.extend(['-hwaccel', AccelerationEngine.str(f.hwaccel_engine)])
            if f.video_decoder != VideoDecoder.Auto:
                args.extend(['-c:v', VideoDecoder.str(f.video_decoder)])
            if len(f.hwaccel_device) > 0:
                args.extend(['-hwaccel_device', f.hwaccel_device])
        if f.log_level != LogLevel.none:
            args.extend(['-loglevel', LogLevel.str(f.log_level)])

        args.extend(['-i', self.__add_double_quotes(f.address)])
        return args

    # noinspection DuplicatedCode
    def build_output(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        args: List[str] = ['-strict', '-2']
        if f.stream_video_codec == StreamVideoCodec.copy:
            args.extend(['-tune', 'zerolatency'])

        # audio starts
        has_size = f.stream_width != 0 and f.stream_height != 0
        if f.stream_audio_codec == AudioCodec.NoAudio:
            args.append('-an')
        else:
            args.extend(['-c:a', AudioCodec.str(f.stream_audio_codec)])
            if f.stream_audio_sample_rate != AudioSampleRate.Auto:
                args.extend(['-ar', AudioSampleRate.str(f.stream_audio_sample_rate)])
            if f.stream_audio_channel != AudioChannel.SOURCE:
                args.extend(['-rematrix_maxval', '1.0', '-ac', AudioChannel.str(f.stream_audio_channel)])
            if f.stream_audio_quality != AudioQuality.Auto:
                args.extend(['-b:a', AudioQuality.str(f.stream_audio_quality)])
            if 0 < f.stream_audio_volume < 100:
                args.extend(['-af', f'"volume={(f.stream_audio_volume / 100.0)}"'])
        # audio ends

        # video starts
        if f.stream_video_codec == StreamVideoCodec.copy:
            args.extend(['-c:v', 'copy'])
        else:
            if f.stream_video_codec != StreamVideoCodec.Auto:
                args.extend(['-c:v', StreamVideoCodec.str(f.stream_video_codec)])
            if has_size:
                args.extend(['-s', f'{f.stream_width}x{f.stream_height}'])
            if f.stream_quality != 0:
                args.extend(['-q:v', str(f.stream_quality)])

            vf_commands = []
            if f.stream_frame_rate > 0:
                vf_commands.append(f'fps={f.stream_frame_rate}')
            if f.stream_rotate != Rotate.No:
                vf_commands.append(Rotate.str(f.stream_rotate))
            if f.stream_video_codec == StreamVideoCodec.H264_VAAPI:
                vf_commands.extend(['format=nv12', 'hwupload'])
                if has_size:
                    vf_commands.append(f'scale_vaapi=w={f.stream_width}:h={f.stream_height}')
            if len(vf_commands) > 0:
                vf_str = '"' + ', '.join(vf_commands) + '"'
                args.extend(['-vf', vf_str])
        # video ends

        args.extend(['-f', 'rtsp' if f.ms_type == MediaServerType.GO_2_RTC else 'flv'])
        args.append(self.__add_double_quotes(f.ms_address))
        return args

    def build_hls_stream(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        if f.stream_type != StreamType.HLS:
            return []
        args: List[str] = ['ffmpeg', '-i', self.__add_double_quotes(f.ms_address)]

        args.extend(['-c:a', 'copy', '-c:v', 'copy'])
        if f.record_file_type == RecordFileTypes.MP4 and f.record_preset != Preset.Auto:
            args.extend(['-preset', Preset.str(f.record_preset)])
        # stream starts
        args.extend(['-tune', 'zerolatency', '-g', '1'])  # acceptable only for HLS
        args.extend(['-f', 'hls'])
        args.extend(['-hls_time', str(f.hls_time)])
        args.extend(['-hls_list_size', str(f.hls_list_size)])
        args.extend(['-start_number', '0'])
        args.extend(['-hls_allow_cache', '0'])
        args.extend(['-hls_flags', '+delete_segments+omit_endlist'])
        args.append(self.__add_double_quotes(get_hls_path(f)))
        return args

    def __build_record(self, duration: int, output_path: str) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        args: List[str] = ['ffmpeg', '-i', self.__add_double_quotes(f.ms_address)]

        if f.record_width != 0 and f.record_height != 0:
            args.extend(['-s', f'{f.record_width}x{f.record_height}'])
        if f.record_quality != 0:
            # Constant Rate Factor (CRF). Use this rate control if you want to keep the best quality and care less about the file size.
            args.extend([f'{"-crf" if f.record_file_type == RecordFileTypes.MP4 else "-q:v"}', str(f.record_quality)])

        # audio starts
        if f.record_audio_codec == AudioCodec.NoAudio:
            args.append('-an')
        else:
            args.extend(['-acodec', AudioCodec.str(f.record_audio_codec)])
            # noinspection DuplicatedCode
            if f.record_audio_sample_rate != AudioSampleRate.Auto:
                args.extend(['-ar', AudioSampleRate.str(f.record_audio_sample_rate)])
            if f.record_audio_channel != AudioChannel.SOURCE:
                args.extend(['-rematrix_maxval', '1.0', '-ac', AudioChannel.str(f.record_audio_channel)])
            if f.record_audio_quality != AudioQuality.Auto:
                args.extend(['-b:a', AudioQuality.str(f.record_audio_quality)])
            if 0 < f.record_audio_volume < 100:
                args.extend(['-af', f'"volume={(f.record_audio_volume / 100.0)}"'])
        # audio ends

        # video starts
        if f.record_video_codec != RecordVideoCodec.Auto:
            args.extend(['-vcodec', RecordVideoCodec.str(f.record_video_codec)])
            vf_commands = []
            if f.record_frame_rate > 0:
                vf_commands.append(f'fps={f.record_frame_rate}')
            if f.record_rotate != Rotate.No:
                vf_commands.append(Rotate.str(f.record_rotate))
            if f.record_video_codec == RecordVideoCodec.H264_VAAPI:
                vf_commands.extend(['format=nv12', 'hwupload'])
            if len(vf_commands) > 0:
                vf_str = '"' + ', '.join(vf_commands) + '"'
                args.extend(['-vf', vf_str])
        # video ends

        args.extend(['-strict', '-2'])
        if f.record_file_type == RecordFileTypes.MP4:
            args.extend(['-movflags', '+faststart'])
        args.extend(['-f', 'segment', '-segment_atclocktime', '1', '-reset_timestamps', '1', '-strftime', '1',
                     '-segment_list', 'pipe:8'])
        if duration < 1:
            duration = 10
        args.extend(['-segment_time', str(duration)])
        args.append(self.__add_double_quotes(os.path.join(output_path, f'%Y_%m_%d_%H_%M_%S.{RecordFileTypes.str(f.record_file_type)}')))
        return args

    def build_record(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        return self.__build_record(f.record_segment_interval * 60, get_record_dir_by(f))  # in minutes

    def build_ai_clip(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model
        return self.__build_record(config.ai.video_clip_duration, get_ai_clip_dir(f))  # in seconds
