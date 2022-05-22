import os
import os.path as path
from typing import List

from common.data.source_model import RecordFileTypes
from common.utilities import logger
from record.concat_demuxer import ConcatDemuxer
from stream.stream_repository import StreamRepository
from utils.dir import get_given_date_record_dir, sort_video_files


class VideoFileMerger:
    def __init__(self, stream_repository: StreamRepository):
        self.stream_repository = stream_repository
        self.cd = ConcatDemuxer(stream_repository)

    @staticmethod
    def __has_error(proc) -> bool:
        try:
            if proc.returncode != 0:
                return True
            err = 'Impossible to open'
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                line = line.decode('utf-8')
                if err in line:
                    return True
                print(line)
        except BaseException as ex2:
            logger.error(f'an error on has error func, err: {ex2}'),
            return True
        return False

    @staticmethod
    def __fix_zeroless_file_name(date_str: str) -> str:
        splits = date_str.split('_')
        values: List[str] = []
        for split in splits:
            value = split
            if int(split) < 10:
                value = '0' + value
            values.append(value)
        return '_'.join(values)

    def merge(self, source_id: str, date_str: str) -> bool:
        source_record_dir = get_given_date_record_dir(source_id, date_str)
        if len(source_record_dir) == 0:
            logger.warning(f'video file merge operation is now exiting since the source_id({source_id}) and/or date_str({date_str}) is invalid')
            return False
        lds = os.listdir(source_record_dir)
        if len(lds) < 2:
            logger.warning(
                f'video file merge operation is now exiting since there is not enough video file for source_id({source_id}) and/or date_str({date_str})')
            return False
        filenames: List[str] = []
        for ld in lds:
            filenames.append(path.join(source_record_dir, ld))
        filenames = sort_video_files(filenames)
        stream_model = self.stream_repository.get(source_id)
        ext = '.' + RecordFileTypes.str(stream_model.record_file_type)
        output_file_name = f'{self.__fix_zeroless_file_name(date_str)}{ext}'
        output_file = path.join(source_record_dir, output_file_name)
        prev_output_file_exists = path.exists(output_file)
        prev_output_file = ''
        if prev_output_file_exists:
            prev_output_file = path.join(source_record_dir, f'prev_{output_file_name}')
            #  move to the prev file
            try:
                os.rename(output_file, prev_output_file)
            except BaseException as ex:
                logger.error(f'an error occurred while moving the prev output file, err: {ex}')
            filenames.remove(output_file)
            filenames.insert(0, prev_output_file)

        proc = None
        try:
            proc = self.cd.concatenate(source_id, filenames, output_file)
            if not self.__has_error(proc):
                for filename in filenames:
                    try:
                        os.remove(filename)
                    except BaseException as ex:
                        logger.error(f'an error occurred while deleting merging file, err: {ex}')
                return True
            else:
                if prev_output_file_exists:
                    os.rename(prev_output_file, output_file)  # rollback the output file
                return False
        finally:
            try:
                if proc is not None:
                    proc.terminate()
            except BaseException as ex:
                logger.error(f'an error occurred while terminating the demuxer subprocess, err:{ex}')
