from builder.models import SourceSettings, InputType, RtspTransport, VideoDecoder, StreamType, StreamVideoCodec, Preset, \
    Rotate, AudioCodec, LogLevel


class CommandBuilder:
    def __init__(self, source_settings: SourceSettings):
        self.source_settings = source_settings

    def build(self):
        s = self.source_settings
        args = ['ffmpeg', '-progress', 'pipe:5']
        # input
        if s.input_type == InputType.H264 and not s.use_camera_timestamp:
            args.extend(['-use_wallclock_as_timestamps', '1'])
        if s.fps > 0:
            args.extend(['-r', str(s.fps)])
        args.extend(['-analyzeduration', str(s.analyzation_duration), '-probesize', str(s.probe_size)])
        args.extend(['-fflags', '+igndts'])
        if s.input_type == InputType.H264 and s.rtsp_transport != RtspTransport.Auto:
            args.extend(['-rtsp_transport', str(s.rtsp_transport)])
        if s.use_hwaccel:
            args.extend(['hwaccel', str(s.hwaccel_engine)])
            if s.video_decoder != VideoDecoder.Auto:
                args.extend(['-c:v', str(s.video_decoder)])
            if not s.hwaccel_device:
                args.extend(['-hwaccel_device', s.hwaccel_device])
        if s.log_level != LogLevel.Info:
            args.extend(['-loglevel', str(s.log_level)])
        if s.input_type == InputType.MPEG4:
            args.append('-re')

        args.extend(['-i', '"' + s.rtsp_address + "'"])

        args.extend(['-strict', '-2'])

        # stream
        # stream audio
        if s.stream_audio_codec == AudioCodec.NoAudio or s.stream_video_codec == AudioCodec.Auto:
            args.append('-an')
        else:
            args.extend(['-c:a', str(s.stream_audio_codec)])

        if s.stream_video_codec == StreamVideoCodec.copy:
            args.extend(['-c:v', 'copy'])
        else:
            if s.stream_video_codec != StreamVideoCodec.Auto:
                args.extend(['-c:v', str(s.stream_video_codec)])
            if s.stream_width != 0 and s.stream_height != 0:
                args.extend(['-s', str(s.stream_width) + 'x' + str(s.stream_height)])
            if s.stream_quality != 0:
                args.extend(['-q:v', str(s.stream_quality)])
            if s.stream_rotate != Rotate.No:
                args.extend(['-vf', '"', str(s.stream_rotate)])
                if len(s.stream_video_filter) > 0:
                    args.extend([',', s.stream_video_filter])
                args.append('"')
            args.extend(['-tune zerolatency', '-g', '1'])  # check if this is also acceptable for non hls

        preset_enabled_type = s.stream_type == StreamType.HLS or s.stream_type == StreamType.MP4
        if preset_enabled_type and s.hls_preset != Preset.Auto:
            args.extend(['-preset', str(s.hls_preset)])

        if s.stream_type == StreamType.HLS:
            args.extend(['-f', 'hls'])
            args.extend(['-hls_time', str(s.hls_time)])
            args.extend(['-hls_list_size', str(s.hls_list_size)])
            args.extend(['-start_number', '0'])
            args.extend(['-hls_allow_cache', '0'])
            args.extend(['-hls_flags', '+delete_segments+omit_endlist'])
            args.append('"' + s.output_file + "'")

        elif s.stream_type == StreamType.MP4 or s.stream_type == StreamType.HEVC_H265:
            if s.stream_type == StreamType.MP4:
                args.extend(['-f', 'mp4'])
        args.extend(['-movflags', '+frag_keyframe+empty_moov+default_base_moof'])
        if s.stream_type == StreamType.MP4:
            args.extend(['-metadata', 'title=MP4 Stream'])
        elif s.stream_type == StreamType.HEVC_H265:
            args.extend(['-metadata', 'title=HVEC H.265 Stream'])
        args.extend(['-reset_timestamps', '1'])
        if s.stream_type == StreamType.HEVC_H265:
            args.extend(['-f', 'hevc'])
        args.append('pipe:1')

