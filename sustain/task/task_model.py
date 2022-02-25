from enum import IntEnum


class TaskOp(IntEnum):
    none = 0
    listen_start_stream_event = 1
    listen_stop_stream_event = 2
    listen_restart_stream_event = 3
    listen_editor_event = 4
    watchdog = 5

    @staticmethod
    def create_dict():
        return {
            TaskOp.listen_start_stream_event: 'listen_start_stream_event',
            TaskOp.listen_stop_stream_event: 'listen_stop_stream_event',
            TaskOp.listen_restart_stream_event: 'listen_restart_stream_event',
            TaskOp.listen_editor_event: 'listen_editor_event',
            TaskOp.watchdog: 'watchdog'
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
