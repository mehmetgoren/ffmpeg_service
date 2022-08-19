from enum import IntEnum


class TaskOp(IntEnum):
    none = 0
    listen_start_stream_event = 1
    listen_stop_stream_event = 2
    listen_restart_stream_event = 3
    listen_editor_event = 4
    listen_various_events = 5
    watchdog = 6
    schedule_video_file_indexer = 7
    execute_various_jobs = 8

    @staticmethod
    def create_dict():
        return {
            TaskOp.listen_start_stream_event: 'listen_start_stream_event',
            TaskOp.listen_stop_stream_event: 'listen_stop_stream_event',
            TaskOp.listen_restart_stream_event: 'listen_restart_stream_event',
            TaskOp.listen_editor_event: 'listen_editor_event',
            TaskOp.listen_various_events: 'listen_various_events',
            TaskOp.watchdog: 'watchdog',
            TaskOp.schedule_video_file_indexer: 'schedule_video_file_indexer',
            TaskOp.execute_various_jobs: 'execute_various_jobs'
        }

    @staticmethod
    def str(value) -> str:
        return TaskOp.create_dict()[value]


class TaskModel:
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
