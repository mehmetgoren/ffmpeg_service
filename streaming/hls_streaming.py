import os
import shutil
import subprocess
from typing import List
import asyncio

import ffmpeg
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size

# for DASH and HLS:
# https://github.com/aminyazdanpanah/python-ffmpeg-video-streaming
# https://video.aminyazdanpanah.com/python?tk=github

# ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,bit_rate -i rtsp://Admin1:Admin1@192.168.0.15/live0 -print_format json
# ffmpeg -v verbose -i rtsp://Admin1:Admin1@192.168.0.15/live0 -vcodec libx264 -acodec aac -f hls -hls_time 5 -g 5 -segment_time 3 -hls_list_size 3 -hls_flags delete_segments /mnt/super/ionix/node/mngr/static/live/stream.m3u8
from redis.client import Redis

from common.utilities import logger
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository


def start_streaming_with_ffmpeg_streaming(rtsp_address='rtsp://Admin1:Admin1@192.168.0.15/live0'):
    probe = ffmpeg.probe(rtsp_address)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])

    video = ffmpeg_streaming.input(rtsp_address)

    # _144p = Representation(Size(256, 144), Bitrate(95 * 1024, 64 * 1024))
    # _240p = Representation(Size(426, 240), Bitrate(150 * 1024, 94 * 1024))
    # _360p = Representation(Size(640, 360), Bitrate(276 * 1024, 128 * 1024))
    # _480p = Representation(Size(854, 480), Bitrate(750 * 1024, 192 * 1024))
    # _720p = Representation(Size(1280, 720), Bitrate(2048 * 1024, 320 * 1024))
    _1080p = Representation(Size(1920, 1080), Bitrate(4096 * 1024, 320 * 1024))

    hls = video.hls(Formats.h264(), vcodec='libx264', acodec='aac', hls_list_size=3, hls_time=5, g=5, segment_time=3)
    # hls.auto_generate_representations()
    # hls.representations(_144p, _240p, _360p, _480p, _720p, _1080p)
    hls.representations(_1080p)
    hls.flags('delete_segments')
    print('streaming is now starting...')
    # hls.output('/mnt/super/ionix/node/ffmpeg_server/streaming/stream.m3u8')
    hls.output('/mnt/super/ionix/node/mngr/static/live/stream.m3u8')
    print()


# def create_ffmpeg_hls_streaming_args(rtsp_address: str, output_file: str) -> List[str]:
#     return ['ffmpeg', '-v', 'verbose', '-i', rtsp_address, '-vcodec', 'libx264', '-acodec', 'aac', '-f',
#             'hls', '-hls_time', '5', '-g', '5', '-segment_time', '3', '-hls_list_size', '3', '-hls_flags',
#             'delete_segments', output_file]


def _create_ffmpeg_hls_streaming_args(rtsp_address: str, output_file: str) -> List[str]:
    return ['ffmpeg', '-i', rtsp_address, '-strict', '-2', '-an', '-c:v', 'copy',
            '-preset', 'ultrafast', '-f', 'hls', '-hls_time', '2', '-hls_list_size', '3',
            '-start_number', '0', '-hls_allow_cache', '0',
            '-hls_flags', 'delete_segments+omit_endlist',
            output_file]


def _delete_files(folder: str):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error('Failed to delete %s. Reason: %s' % (file_path, e))


def start_streaming(model: StreamingModel, connection: Redis):
    rtsp_address, output_file = model.rtsp_address, model.output_file

    logger.info('starting streaming')
    args: List[str] = _create_ffmpeg_hls_streaming_args(rtsp_address, output_file)

    p = subprocess.Popen(args)
    try:
        model.pid = p.pid
        model.args = ' '.join(args)
        rep = StreamingRepository(connection)
        rep.add(model)
        logger.info('the model has been saved by repository')
        logger.info('streaming subprocess has been opened')
        _delete_files(os.path.dirname(model.output_file))
        p.wait()
    except Exception as e:
        logger.error(f'An error occurred while starting FFmpeg sub-process, err: {e}')
    finally:
        p.terminate()
        logger.info('streaming subprocess has been terminated')

    return p.returncode


async def start_streaming_async(model: StreamingModel, connection: Redis):
    rtsp_address, output_file = model.rtsp_address, model.output_file

    logger.info('starting streaming')
    args = ' '.join(_create_ffmpeg_hls_streaming_args(rtsp_address, output_file))

    p = await asyncio.create_subprocess_shell(args)
    try:
        model.pid = p.pid
        model.args = ' '.join(args)
        rep = StreamingRepository(connection)
        rep.add(model)
        logger.info('the model has been saved by repository')
        logger.info('streaming subprocess has been opened')
        await p.wait()
    except Exception as e:
        logger.error(f'An error occurred while starting FFmpeg sub-process, err: {e}')
    finally:
        p.terminate()
        logger.info('streaming subprocess has been terminated')

    return p.returncode
