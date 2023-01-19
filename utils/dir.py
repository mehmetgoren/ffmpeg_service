from __future__ import annotations

import os
import pathlib
import sys
from os import path
from pathlib import Path
from datetime import datetime
from typing import List

from common.data.source_model import FFmpegModel
from common.utilities import config, logger, fix_zero, fix_zero_s
from stream.stream_model import StreamModel


def create_dir_if_not_exists(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def __get_root_path(model: FFmpegModel | StreamModel) -> str:
    dir_paths = config.general.dir_paths
    if len(dir_paths) == 0:
        logger.fatal('config.general.dir_paths is empty, the program will be terminated')
        sys.exit('config.general.dir_paths is empty')
    root_path = dir_paths[0] if len(model.root_dir_path) == 0 else model.root_dir_path
    return root_path


def get_record_dir_by(model: FFmpegModel | StreamModel) -> str:
    root_path = __get_root_path(model)
    return path.join(root_path, 'record', model.id)


def get_stream_dir(model: FFmpegModel) -> str:
    root_path = __get_root_path(model)
    return os.path.join(root_path, 'stream', model.id)


def get_ai_clip_dir(ffmpeg_model: FFmpegModel) -> str:
    return path.join(get_record_dir_by(ffmpeg_model), 'ai')


def get_hls_path(ffmpeg_model: FFmpegModel | StreamModel) -> str:
    return os.path.join(get_stream_dir(ffmpeg_model), 'stream.m3u8')


def get_filename_date_record_dir(stream_model: StreamModel, filename: str) -> str:
    dt = filename_to_datetime(filename)
    if dt is None:
        return ''
    ti = TimeIndex()
    ti.set_values(dt)
    root_path = get_record_dir_by(stream_model)
    return ti.get_indexed_path(root_path)


def get_given_date_record_dir(stream_model: StreamModel, date_str: str) -> str:
    sep = '_'
    splits = date_str.split(sep)
    if len(splits) != 4:
        return ''
    ti = TimeIndex(splits[0], splits[1], splits[2], splits[3])
    root_path = get_record_dir_by(stream_model)
    return ti.get_indexed_path(root_path)


class TimeIndex:
    def __init__(self, year: str = '', month: str = '', day: str = '', hour: str = ''):
        self.year: str = year
        self.month: str = fix_zero_s(month)
        self.day: str = fix_zero_s(day)
        self.hour: str = fix_zero_s(hour)

    def set_values(self, date: datetime):
        self.year: str = str(date.year)
        self.month: str = fix_zero(date.month)
        self.day: str = fix_zero(date.day)
        self.hour: str = fix_zero(date.hour)

    def get_indexed_path(self, root_path: str) -> str:
        return path.join(root_path, self.year, self.month, self.day, self.hour)


def sort_video_files(filenames: List[str]) -> List[str]:
    items: List[_FileInfo] = []
    for filename in filenames:
        fi = _FileInfo(filename)
        if fi.date is not None:
            items.append(fi)
    items.sort()
    return [item.filename for item in items]


def get_sorted_valid_files(dir_path: str, ext: str) -> List[str]:
    all_files = os.listdir(dir_path)
    ret: List[str] = []
    for f in all_files:
        full_path = path.join(dir_path, f)
        if path.isdir(full_path) or pathlib.Path(f).suffix != ext:
            continue
        ret.append(full_path)
    return sort_video_files(ret)


def filename_to_datetime(filename: str) -> datetime | None:
    try:
        filename = Path(filename).stem
        return str_to_datetime(filename)
    except BaseException as ex:
        logger.error(f'an error occurred on filename_to_datetime, err: {ex}')
        return None


def str_to_datetime(value: str) -> datetime | None:
    try:
        sep = '_'
        splits = value.split(sep)

        year = int(splits[0])
        length = len(splits)
        month = int(splits[1]) if length > 1 else 1
        day = int(splits[2]) if length > 2 else 1
        hour = int(splits[3]) if length > 3 else 0
        minute = int(splits[4]) if length > 4 else 0
        second = int(splits[5]) if length > 5 else 0
        microsecond = int(splits[6]) if length > 6 else 0

        return datetime(year, month, day, hour, minute, second, microsecond)
    except BaseException as ex:
        logger.error(f'an error occurred on str_to_datetime, err: {ex}')
        return None


class _FileInfo:
    def __init__(self, filename: str):  # filename format: 2022_04_18_19_01_11.mp4
        self.filename: str = filename
        self.date = filename_to_datetime(filename)
        self.sep = '_'

    def __lt__(self, other):
        return self.date < other.date
