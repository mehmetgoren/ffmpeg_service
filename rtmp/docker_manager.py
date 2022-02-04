from typing import List, Any

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

    def create_rtmp_model(self, type: RmtpServerType, unique_name: str) -> BaseRtmpModel:
        if type == RmtpServerType.SRS:
            return SrsRtmpModel(unique_name, self.connection)
        elif type == RmtpServerType.LIVEGO:
            return LiveGoRtmpModel(unique_name, self.connection)
        elif type == RmtpServerType.NODE_MEDIA_SERVER:
            return NodeMediaServerRtmpModel(unique_name, self.connection)
        raise NotImplementedError('RmtpServerType was not match')

    def __create_rtmp_model(self, rtmp_server_type: RmtpServerType, streaming_id: str) -> BaseRtmpModel:
        rtmp_model = self.create_rtmp_model(rtmp_server_type, streaming_id)

        rtmp_model.int_ports()

        return rtmp_model

    def __init_container(self, rtmp_model: BaseRtmpModel, all_containers: List):
        container_name = rtmp_model.get_container_name()
        for container in all_containers:
            if container.name == container_name:
                container.stop()
                container.remove()
                break
        container = self.client.containers.run(rtmp_model.get_image_name(), detach=True,
                                               command=rtmp_model.get_commands(),
                                               # auto_remove=True, remove=True,
                                               restart_policy={'Name': 'unless-stopped'},
                                               name=container_name,
                                               ports=rtmp_model.get_ports())
        return container

    def run(self, rtmp_server_type: RmtpServerType, streaming_id: str) -> (BaseRtmpModel, Any):
        rtmp_model = self.__create_rtmp_model(rtmp_server_type, streaming_id)
        all_containers = self.client.containers.list(all=True)
        container = self.__init_container(rtmp_model, all_containers)
        return rtmp_model, container

    # Use it if you decide to use auto_remove on containers. Otherwise, 'unless stopped' can restore de container and don't use it on the process checker.
    def run_all(self, streaming_repository: StreamingRepository):
        all_containers = self.client.containers.list(all=True)
        models = streaming_repository.get_all()
        filtered_models: List[StreamingModel] = []
        for model in models:
            if model.rtmp_server_type == StreamType.FLV:
                filtered_models.append(model)
        for streaming_model in filtered_models:
            if not streaming_model.rtmp_server_initialized:
                rtmp_model = self.__create_rtmp_model(streaming_model.rtmp_server_type, streaming_model.id)
                self.__init_container(rtmp_model, all_containers)
                rtmp_model.map_to(streaming_model)
                streaming_repository.add(streaming_model)

    def remove(self, model: StreamingModel):
        container = self.get_container(model)
        if container is not None:
            container.stop()
            container.remove()

    def get_container(self, model: StreamingModel):
        container_name = model.rtmp_container_name
        containers = self.client.containers.list(all=True)
        for container in containers:
            if container.name == container_name:
                return container
        return None
