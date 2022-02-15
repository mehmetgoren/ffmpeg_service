from enum import IntEnum


class TaskOp(IntEnum):
    none = 0
    listen_start_stream_event = 1
    listen_stop_stream_event = 2
    listen_restart_stream_event = 3
    listen_editor_event = 4
    check_leaky_ffmpeg_processes = 5
    check_unstopped_rtmp_server_containers = 6
    check_ffmpeg_stream_running_process = 7
    check_ffmpeg_record_running_process = 8

    @staticmethod
    def create_dict():
        return {
            TaskOp.listen_start_stream_event: 'listen_start_stream_event',
            TaskOp.listen_stop_stream_event: 'listen_stop_stream_event',
            TaskOp.listen_restart_stream_event: 'listen_restart_stream_event',
            TaskOp.listen_editor_event: 'listen_editor_event',
            TaskOp.check_leaky_ffmpeg_processes: 'check_leaky_ffmpeg_processes',
            TaskOp.check_unstopped_rtmp_server_containers: 'check_unstopped_rtmp_server_containers',
            TaskOp.check_ffmpeg_stream_running_process: 'check_ffmpeg_stream_running_process',
            TaskOp.check_ffmpeg_record_running_process: 'check_ffmpeg_record_running_process',
        }

    @staticmethod
    def str(value) -> str:
        return TaskOp.create_dict()[value]


class Task:
    def __init__(self):
        self.op: TaskOp = TaskOp.none
        self.op_name: str = ''

        self.job_id: str = ''
        self.worker_name: str = ''
        self.pid: int = 0
        self.worker_pid: int = 0

        self.exception_msg: str = ''
        self.failed_count: int = 0

    def set_op(self, op: TaskOp):
        self.op = op
        self.op_name = TaskOp.str(op)
