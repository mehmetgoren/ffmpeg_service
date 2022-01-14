import subprocess
from typing import List

from redis.client import Redis

from common.utilities import logger
from data.models import RecordingModel
from data.recording_repository import RecordingRepository


# ffmpeg -progress pipe:5 -use_wallclock_as_timestamps 1 -analyzeduration 1000000 -probesize 1000000
# -fflags +igndts -rtsp_transport tcp -loglevel warning
# -i rtsp://admin12:admin12@192.168.0.29:554/stream1
# -strict -2 -an -c:v copy -preset ultrafast -f hls -hls_time 2 -hls_list_size 3 -start_number 0
# -hls_allow_cache 0 -hls_flags +delete_segments+omit_endlist /dev/shm/streams/hLucmCjGfv/OvkzcGHguU/s.m3u8
# -an -vcodec copy -strict -2 -movflags +faststart -f segment -segment_atclocktime 1 -reset_timestamps 1 -strftime 1
# -segment_list pipe:8 -segment_time 900 /home/Shinobi/videos2/hLucmCjGfv/OvkzcGHguU/%Y-%m-%dT%H-%M-%S.mp4

def _create_ffmpeg_mp4_recording_args(model: RecordingModel) -> List[str]:
    rtsp_address, duration, output_file = model.rtsp_address, model.duration, model.output_file
    return ['ffmpeg', '-i', rtsp_address, '-an', '-vcodec', 'copy', '-strict', '-2', '-movflags', '+faststart',
            '-rtsp_transport', 'tcp',
            '-f', 'segment', '-segment_atclocktime', '1', '-reset_timestamps', '1', '-strftime', '1',
            '-segment_list', 'pipe:8', '-segment_time', str(duration * 60),
            model.output_file + '/%Y-%m-%d-%H-%M-%S.mp4']


def start_recording(connection: Redis, model: RecordingModel):
    logger.info('starting recording')
    args: List[str] = _create_ffmpeg_mp4_recording_args(model)

    p = subprocess.Popen(args)
    try:
        model.pid = p.pid
        model.args = ' '.join(args)
        rep = RecordingRepository(connection)
        rep.add(model)
        logger.info('the model has been saved by repository')
        logger.info('recording subprocess has been opened')
        p.wait()
    except Exception as e:
        logger.error(f'an error occurred while starting FFmpeg sub-process, err: {e}')
    finally:
        p.terminate()
        logger.info('recording subprocess has been terminated')

    return p.returncode
