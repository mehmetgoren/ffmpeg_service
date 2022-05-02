import os
from os import path
from typing import List
import ffmpeg

from common.data.source_model import RecordFileTypes
from common.utilities import config, logger
from stream.stream_repository import StreamRepository
from utils.dir import get_record_dir_by, get_filename_date_record_dir, create_dir_if_not_exists, get_sorted_valid_files


class VideoFileIndexer:
    def __init__(self, stream_repository: StreamRepository):
        self.stream_repository = stream_repository
        self.last_file_count = config.ffmpeg.record_concat_limit
        if self.last_file_count < 1:
            self.last_file_count = 1

    @staticmethod
    def __remove_invalid_midget_files(filenames: List[str]) -> List[str]:
        ret = []
        for filename in filenames:
            file_size = path.getsize(filename)
            if file_size < 1024:
                try:
                    os.remove(filename)
                except BaseException as ex:
                    logger.error(f'an error occurred while removing midget files, err: {ex}')
                logger.warn(f'a invalid file size({file_size}) found on a valid video file({filename}) and removed')
                continue
            ret.append(filename)
        return ret

    @staticmethod
    def __check_by_ffprobe(filenames: List[str]) -> List[str]:
        valid_list: List[str] = []
        for filename in filenames:
            try:
                probe_result = ffmpeg.probe(filename)
                print(probe_result)
                valid_list.append(filename)
            except BaseException as ex:
                os.remove(filename)
                logger.warn(f'a corrupted video file({filename}) was found and deleted, ex: {ex}')
        return valid_list

    def move(self, source_id: str):
        source_record_dir = get_record_dir_by(source_id)
        stream_model = self.stream_repository.get(source_id)
        if stream_model is None:
            logger.info(f'no stream({source_id}) was found for move operation')
            return
        ext = '.' + RecordFileTypes.str(stream_model.record_file_type)
        filenames = get_sorted_valid_files(source_record_dir, ext)
        valid_file_length = len(filenames) - self.last_file_count
        if valid_file_length < 1:
            logger.info(f'no valid record file({ext}) was found on source({source_id}) record parent directory')
            return
        filenames = filenames[0:valid_file_length]
        filenames: List[str] = self.__remove_invalid_midget_files(filenames)
        if len(filenames) == 0:
            logger.info(f'no valid record file({ext}) was found on source({source_id}) record parent directory')
            return
        filenames = self.__check_by_ffprobe(filenames)
        if len(filenames) == 0:
            logger.info(f'no valid record file({ext}) was found on source({source_id}) record parent directory')
            return

        for filename in filenames:
            dest_dir = get_filename_date_record_dir(source_id, filename)
            create_dir_if_not_exists(dest_dir)
            dest_filename = path.join(dest_dir, path.basename(filename))
            try:
                os.rename(filename, dest_filename)
            except BaseException as ex:
                logger.error(f'an error occurred while moving files to indexed folders, err: {ex}')
            logger.info(f'{filename} was removed to {dest_filename}')
