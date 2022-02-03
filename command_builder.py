import os
from typing import List

from common.data.source_model import FFmpegModel, InputType, RtspTransport, VideoDecoder, StreamType, \
    StreamVideoCodec, Preset, Rotate, AudioCodec, LogLevel, AudioChannel, AudioQuality, AudioSampleRate, \
    RecordFileTypes, RecordVideoCodec, AccelerationEngine
from common.utilities import config


def get_hls_output_path(source_id: str):
    return os.path.join(config.path.streaming, source_id, 'stream.m3u8')


def get_read_jpeg_output_path(source_id: str):
    return os.path.join(config.path.reading, source_id, 's.jpeg')


def get_recording_output_folder_path(source_id: str):
    return os.path.join(config.path.recording, source_id)


class CommandBuilder:
    def __init__(self, source_model: FFmpegModel):
        self.ffmpeg_model: FFmpegModel = source_model
        self.use_double_quotes_for_path: bool = False

    def __add_double_quotes(self, path: str):
        if self.use_double_quotes_for_path:
            path = f'"{path}"'
        return path

    # noinspection DuplicatedCode
    def build(self) -> List[str]:
        f: FFmpegModel = self.ffmpeg_model

        args: List[str] = ['ffmpeg', '-progress', 'pipe:5']

        # input starts
        use_wallclock = f.input_type == InputType.H264_H265 and f.use_camera_timestamp
        if use_wallclock:
            args.extend(['-use_wallclock_as_timestamps', '1'])  # cause delay, check it
        if f.input_frame_rate > 0:
            args.extend(['-r', str(f.input_frame_rate)])
        args.extend(['-analyzeduration', str(f.analyzation_duration), '-probesize', str(f.probe_size)])
        args.extend(['-fflags', '+igndts'])
        if f.input_type == InputType.H264_H265 and f.rtsp_transport != RtspTransport.Auto:
            args.extend(['-rtsp_transport', RtspTransport.str(f.rtsp_transport)])
        if f.use_hwaccel:
            args.extend(['-hwaccel', AccelerationEngine.str(f.hwaccel_engine)])
            if f.video_decoder != VideoDecoder.Auto:
                args.extend(['-c:v', VideoDecoder.str(f.video_decoder)])
            if len(f.hwaccel_device) > 0:
                args.extend(['-hwaccel_device', f.hwaccel_device])
        if f.log_level != LogLevel.none:
            args.extend(['-loglevel', LogLevel.str(f.log_level)])
        if f.input_type == InputType.MPEG4:
            args.append('-re')

        args.extend(['-i', self.__add_double_quotes(f.rtsp_address)])

        args.extend(['-strict', '-2'])
        # input ends

        # stream starts
        # audio
        has_size = f.stream_width != 0 and f.stream_height != 0
        if f.stream_audio_codec == AudioCodec.NoAudio or f.stream_video_codec == AudioCodec.Auto:
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

        if f.hls_preset != Preset.Auto:
            args.extend(['-preset', Preset.str(f.hls_preset)])

        if f.stream_type == StreamType.HLS:
            args.extend(['-tune', 'zerolatency', '-g', '1'])  # acceptable only for HLS
            args.extend(['-f', 'hls'])
            args.extend(['-hls_time', str(f.hls_time)])
            args.extend(['-hls_list_size', str(f.hls_list_size)])
            args.extend(['-start_number', '0'])
            args.extend(['-hls_allow_cache', '0'])
            args.extend(['-hls_flags', '+delete_segments+omit_endlist'])
            args.append(self.__add_double_quotes(get_hls_output_path(f.id)))

        elif f.stream_type == StreamType.FLV:
            args.extend(['-f', 'flv'])
            args.append(self.__add_double_quotes(f.rtmp_server_address))
        # stream ends

        # JPEG Snapshot starts
        if f.jpeg_enabled:
            jpeg_fps = 1 if f.jpeg_frame_rate < 1 else f.jpeg_frame_rate
            args.extend(['-vf', f'fps={jpeg_fps}'])
            if f.jpeg_width > 0 and f.jpeg_height > 0:
                args.extend(['-s', f'{f.jpeg_width}x{f.jpeg_height}'])
            if 1 < f.jpeg_quality < 32:
                args.extend(['-q:v', str(f.jpeg_quality)])
            args.extend(['-r', str(jpeg_fps)])
            if f.jpeg_use_vsync:
                args.extend(['-vsync', 'vfr'])
            args.extend(['-update', '1', self.__add_double_quotes(get_read_jpeg_output_path(f.id)), '-y'])
        # JPEG Snapshot ends

        # Recording starts
        if f.recording:
            if f.record_width != 0 and f.record_height != 0:
                args.extend(['-s', f'{f.record_width}x{f.record_height}'])
            if f.record_quality != 0:
                # Constant Rate Factor (CRF). Use this rate control if you want to keep the best quality and care less about the file size.
                args.extend(
                    [f'{"-crf" if f.record_file_type == RecordFileTypes.MP4 else "-q:v"}', str(f.record_quality)])

            # audio starts
            if f.record_video_codec == AudioCodec.NoAudio or f.record_video_codec == AudioCodec.Auto:
                args.append('-an')
            else:
                args.extend(['-acodec', AudioCodec.str(f.record_audio_codec)])
                if f.record_audio_sample_rate != AudioSampleRate.Auto:
                    args.extend(['-ar', AudioSampleRate.str(f.record_audio_sample_rate)])
                if f.record_audio_channel != AudioChannel.SOURCE:
                    args.extend(['-rematrix_maxval', '1.0', '-ac', AudioChannel.str(f.record_audio_channel)])
                if f.record_audio_quality != AudioQuality.Auto:
                    args.extend(['-b:a', AudioQuality.str(f.record_audio_quality)])
                if 0 < f.record_audio_volume < 100:
                    args.extend(['-af', f'"volume={(f.record_audio_volume / 100.0)}"'])
            # audio ends

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
            if f.record_file_type == RecordFileTypes.MP4 and f.record_preset != Preset.Auto:
                args.extend(['-preset', Preset.str(f.record_preset)])
            args.extend(['-strict', '-2'])
            if f.record_file_type == RecordFileTypes.MP4:
                args.extend(['-movflags', '+faststart'])
            args.extend(['-f', 'segment', '-segment_atclocktime', '1', '-reset_timestamps', '1', '-strftime', '1',
                         '-segment_list', 'pipe:8'])
            if f.record_segment_interval < 1:
                f.record_segment_interval = 15
            args.extend(['-segment_time', str(f.record_segment_interval * 60)])
            args.append(self.__add_double_quotes(os.path.join(get_recording_output_folder_path(f.id),
                                                              f'%Y-%m-%d-%H-%M-%S.{RecordFileTypes.str(f.record_file_type)}')))
        # Recording ends
        return args
