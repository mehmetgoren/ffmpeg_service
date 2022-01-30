import os
from typing import List

from common.data.source_model import SourceModel, InputType, RtspTransport, VideoDecoder, StreamType, \
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
    def __init__(self, source_model: SourceModel):
        self.source_model: SourceModel = source_model
        # todo: remove to Config
        self.use_double_quotes_for_path: bool = False

    def __add_double_quotes(self, path: str):
        if self.use_double_quotes_for_path:
            path = f'"{path}"'
        return path

    # noinspection DuplicatedCode
    def build(self) -> List[str]:
        s: SourceModel = self.source_model

        args: List[str] = ['ffmpeg', '-progress', 'pipe:5']

        # input starts
        use_wallclock = s.input_type == InputType.H264_H265 and s.use_camera_timestamp
        if use_wallclock:
            args.extend(['-use_wallclock_as_timestamps', '1'])  # cause delay, check it
        if s.input_frame_rate > 0:
            args.extend(['-r', str(s.input_frame_rate)])
        args.extend(['-analyzeduration', str(s.analyzation_duration), '-probesize', str(s.probe_size)])
        args.extend(['-fflags', '+igndts'])
        if s.input_type == InputType.H264_H265 and s.rtsp_transport != RtspTransport.Auto:
            args.extend(['-rtsp_transport', RtspTransport.str(s.rtsp_transport)])
        if s.use_hwaccel:
            args.extend(['-hwaccel', AccelerationEngine.str(s.hwaccel_engine)])
            if s.video_decoder != VideoDecoder.Auto:
                args.extend(['-c:v', VideoDecoder.str(s.video_decoder)])
            if len(s.hwaccel_device) > 0:
                args.extend(['-hwaccel_device', s.hwaccel_device])
        if s.log_level != LogLevel.none:
            args.extend(['-loglevel', LogLevel.str(s.log_level)])
        if s.input_type == InputType.MPEG4:
            args.append('-re')

        # args.extend(['-i', '"' + s.rtsp_address + '"'])
        args.extend(['-i', s.rtsp_address])

        args.extend(['-strict', '-2'])
        # input ends

        # stream starts
        # audio
        has_size = s.stream_width != 0 and s.stream_height != 0
        if s.stream_audio_codec == AudioCodec.NoAudio or s.stream_video_codec == AudioCodec.Auto:
            args.append('-an')
        else:
            args.extend(['-c:a', AudioCodec.str(s.stream_audio_codec)])
            if s.stream_audio_sample_rate != AudioSampleRate.Auto:
                args.extend(['-ar', AudioSampleRate.str(s.stream_audio_sample_rate)])
            if s.stream_audio_channel != AudioChannel.SOURCE:
                args.extend(['-rematrix_maxval', '1.0', '-ac', AudioChannel.str(s.stream_audio_channel)])
            if s.stream_audio_quality != AudioQuality.Auto:
                args.extend(['-b:a', AudioQuality.str(s.stream_audio_quality)])
            if 0 < s.stream_audio_volume < 100:
                args.extend(['-af', f'"volume={(s.stream_audio_volume / 100.0)}"'])

        if s.stream_video_codec == StreamVideoCodec.copy:
            args.extend(['-c:v', 'copy'])
        else:
            if s.stream_video_codec != StreamVideoCodec.Auto:
                args.extend(['-c:v', StreamVideoCodec.str(s.stream_video_codec)])
            if has_size:
                args.extend(['-s', f'{s.stream_width}x{s.stream_height}'])
            if s.stream_quality != 0:
                args.extend(['-q:v', str(s.stream_quality)])

            vf_commands = []
            if s.stream_frame_rate > 0:
                vf_commands.append(f'fps={s.stream_frame_rate}')
            if s.stream_rotate != Rotate.No:
                vf_commands.append(Rotate.str(s.stream_rotate))
            if s.stream_video_codec == StreamVideoCodec.H264_VAAPI:
                vf_commands.extend(['format=nv12', 'hwupload'])
                if has_size:
                    vf_commands.append(f'scale_vaapi=w={s.stream_width}:h={s.stream_height}')
            if len(vf_commands) > 0:
                vf_str = '"' + ', '.join(vf_commands) + '"'
                args.extend(['-vf', vf_str])

        if s.hls_preset != Preset.Auto:
            args.extend(['-preset', Preset.str(s.hls_preset)])

        if s.stream_type == StreamType.HLS:
            args.extend(['-tune', 'zerolatency', '-g', '1'])  # acceptable only for HLS
            args.extend(['-f', 'hls'])
            args.extend(['-hls_time', str(s.hls_time)])
            args.extend(['-hls_list_size', str(s.hls_list_size)])
            args.extend(['-start_number', '0'])
            args.extend(['-hls_allow_cache', '0'])
            args.extend(['-hls_flags', '+delete_segments+omit_endlist'])
            args.append(self.__add_double_quotes(get_hls_output_path(s.id)))

        elif s.stream_type == StreamType.FLV:
            args.extend(['-f', 'flv'])
            args.append('"' + s.flv_address + '"')
        # stream ends

        # JPEG Snapshot starts
        if s.jpeg_enabled:
            args.extend(['-vf', f'fps={1 if s.jpeg_frame_rate < 1 else s.jpeg_frame_rate}'])
            if s.jpeg_width > 0 and s.jpeg_height > 0:
                args.extend(['-s', f'{s.jpeg_width}x{s.jpeg_height}'])
                args.extend(
                    ['-update', '1', self.__add_double_quotes(os.path.join(get_read_jpeg_output_path(s.id), 's.jpg')),
                     '-y'])
        # JPEG Snapshot ends

        # Recording starts
        if s.recording:
            if s.record_width != 0 and s.record_height != 0:
                args.extend(['-s', f'{s.record_width}x{s.record_height}'])
            if s.record_quality != 0:
                # Constant Rate Factor (CRF). Use this rate control if you want to keep the best quality and care less about the file size.
                args.extend(
                    [f'{"-crf" if s.record_file_type == RecordFileTypes.MP4 else "-q:v"}', str(s.record_quality)])

            # audio starts
            if s.record_video_codec == AudioCodec.NoAudio or s.record_video_codec == AudioCodec.Auto:
                args.append('-an')
            else:
                args.extend(['-acodec', AudioCodec.str(s.record_audio_codec)])
                if s.record_audio_sample_rate != AudioSampleRate.Auto:
                    args.extend(['-ar', AudioSampleRate.str(s.record_audio_sample_rate)])
                if s.record_audio_channel != AudioChannel.SOURCE:
                    args.extend(['-rematrix_maxval', '1.0', '-ac', AudioChannel.str(s.record_audio_channel)])
                if s.record_audio_quality != AudioQuality.Auto:
                    args.extend(['-b:a', AudioQuality.str(s.record_audio_quality)])
                if 0 < s.record_audio_volume < 100:
                    args.extend(['-af', f'"volume={(s.record_audio_volume / 100.0)}"'])
            # audio ends

            if s.record_video_codec != RecordVideoCodec.Auto:
                args.extend(['-vcodec', RecordVideoCodec.str(s.record_video_codec)])
                vf_commands = []
                if s.record_frame_rate > 0:
                    vf_commands.append(f'fps={s.record_frame_rate}')
                if s.record_rotate != Rotate.No:
                    vf_commands.append(Rotate.str(s.record_rotate))
                if s.record_video_codec == RecordVideoCodec.H264_VAAPI:
                    vf_commands.extend(['format=nv12', 'hwupload'])
                if len(vf_commands) > 0:
                    vf_str = '"' + ', '.join(vf_commands) + '"'
                    args.extend(['-vf', vf_str])
            if s.record_file_type == RecordFileTypes.MP4 and s.record_preset != Preset.Auto:
                args.extend(['-preset', Preset.str(s.record_preset)])
            args.extend(['-strict', '-2'])
            if s.record_file_type == RecordFileTypes.MP4:
                args.extend(['-movflags', '+faststart'])
            args.extend(['-f', 'segment', '-segment_atclocktime', '1', '-reset_timestamps', '1', '-strftime', '1',
                         '-segment_list', 'pipe:8'])
            if s.record_segment_interval < 1:
                s.record_segment_interval = 15
            args.extend(['-segment_time', str(s.record_segment_interval * 60)])
            args.append(self.__add_double_quotes(os.path.join(get_recording_output_folder_path(s.id),
                                                              f'%Y-%m-%d-%H-%M-%S.{RecordFileTypes.str(s.record_file_type)}')))
        # Recording ends
        return args
