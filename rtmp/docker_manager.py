import json
from typing import List

import docker
from redis.client import Redis

from common.data.source_model import StreamType
from streaming.streaming_model import StreamingModel, RmtpServerType
from streaming.streaming_repository import StreamingRepository
from rtmp.rtmp_models import BaseRtmpModel, SrsRtmpModel, LiveGoRtmpModel, NodeMediaServerRtmpModel


# for more info: https://docker-py.readthedocs.io/en/stable/containers.html
class DockerManager:
    def __init__(self, connection: Redis):
        self.connection: Redis = connection
        self.client = docker.from_env()
        self.containers: list = []

    def create_rtmp_model(self, type: RmtpServerType, unique_name: str) -> BaseRtmpModel:
        if type == RmtpServerType.SRS:
            return SrsRtmpModel(unique_name, self.connection)
        elif type == RmtpServerType.LIVEGO:
            return LiveGoRtmpModel(unique_name, self.connection)
        elif type == RmtpServerType.NODE_MEDIA_SERVER:
            return NodeMediaServerRtmpModel(unique_name, self.connection)
        raise NotImplementedError('RmtpServerType was not match')

    def run(self):
        rep = StreamingRepository(self.connection)
        models = rep.get_all()
        filtered_models: List[StreamingModel] = []
        for model in models:
            if model.rtmp_server_type == StreamType.FLV:
                filtered_models.append(model)
        for streaming_model in filtered_models:
            if not streaming_model.rtmp_server_initialized:
                rtmp_model = self.create_rtmp_model(streaming_model.rtmp_server_type, streaming_model.id)

                ports = rtmp_model.int_ports()
                streaming_model.rtmp_container_ports = json.dumps(ports)

                streaming_model.rtmp_image_name = rtmp_model.get_image_name()
                streaming_model.rtmp_container_name = rtmp_model.get_container_name()
                streaming_model.rtmp_address = rtmp_model.get_rtmp_address()
                streaming_model.rtmp_flv_address = rtmp_model.get_flv_address()
                streaming_model.rtmp_container_commands = ','.join(rtmp_model.get_commands())

                streaming_model.rtmp_server_initialized = True
                rep.replace(streaming_model)

            all_containers = self.client.containers.list(all=True)
            found = False
            _container = None
            for container in all_containers:
                if container.name == streaming_model.rtmp_container_name:
                    if container.status != 'running':
                        container.start()  # check it if it blocks the thread
                    _container = container
                    found = True
            if not found:
                _container = self.client.containers.run(streaming_model.rtmp_image_name, detach=True,
                                                        command=streaming_model.rtmp_container_commands.split(','),
                                                        # auto_remove=True, remove=True,
                                                        restart_policy={'Name': 'unless-stopped'},
                                                        name=streaming_model.rtmp_container_name,
                                                        ports=json.loads(streaming_model.rtmp_container_ports))
            self.containers.append(_container)

    # call this method when a source was deleted
    def remove(self, model: StreamingModel):
        container_name = model.rtmp_container_name
        for container in self.containers:
            if container.name == container_name:
                container.remove()
                break
