from typing import List, Any
import docker
from redis.client import Redis

from stream.stream_model import StreamModel, RmtpServerType
from rtmp.rtmp_models import BaseRtmpModel, SrsRtmpModel, SrsRealtimeRtmpServer, LiveGoRtmpModel, NodeMediaServerRtmpModel


# for more info: https://docker-py.readthedocs.io/en/stable/containers.html
class DockerManager:
    def __init__(self, connection: Redis):
        self.connection: Redis = connection
        self.client = docker.from_env()

    def __create_rtmp_model(self, rtmp_server_type: RmtpServerType, stream_id: str) -> BaseRtmpModel:
        if rtmp_server_type == RmtpServerType.SRS:
            rtmp_model = SrsRtmpModel(stream_id, self.connection)
        elif rtmp_server_type == RmtpServerType.SRS_REALTIME:
            rtmp_model = SrsRealtimeRtmpServer(stream_id, self.connection)
        elif rtmp_server_type == RmtpServerType.LIVEGO:
            rtmp_model = LiveGoRtmpModel(stream_id, self.connection)
        elif rtmp_server_type == RmtpServerType.NODE_MEDIA_SERVER:
            rtmp_model = NodeMediaServerRtmpModel(stream_id, self.connection)
        else:
            raise NotImplementedError('RmtpServerType was not match')

        rtmp_model.int_ports()

        return rtmp_model

    def __init_container(self, rtmp_model: BaseRtmpModel, all_containers: List):
        container_name = rtmp_model.get_container_name()
        for container in all_containers:
            if container.name == container_name:
                self.stop_container(container)
                break
        container = self.client.containers.run(rtmp_model.get_image_name(), detach=True,
                                               command=rtmp_model.get_commands(),
                                               # auto_remove=True, remove=True,
                                               restart_policy={'Name': 'unless-stopped'},
                                               name=container_name,
                                               ports=rtmp_model.get_ports())
        return container

    def run(self, rtmp_server_type: RmtpServerType, stream_id: str) -> (BaseRtmpModel, Any):
        rtmp_model = self.__create_rtmp_model(rtmp_server_type, stream_id)
        all_containers = self.client.containers.list(all=True)
        container = self.__init_container(rtmp_model, all_containers)
        return rtmp_model, container

    def remove(self, model: StreamModel):
        container = self.get_container(model)
        if container is not None:
            self.stop_container(container)

    def get_container_by(self, container_name):
        filters: dict = {'name': container_name}
        containers = self.client.containers.list(filters=filters)
        return containers[0] if len(containers) > 0 else None

    def get_container(self, model: StreamModel):
        container_name = model.rtmp_container_name
        containers = self.client.containers.list(all=True)
        for container in containers:
            if container.name == container_name:
                return container
        return None

    def get_all_containers(self):
        return self.client.containers.list(all=True)

    @staticmethod
    def stop_container(container):
        container.stop()
        container.remove()

    @staticmethod
    def parse_image_name(container):
        return container.image.tags[0].replace(':latest', '')
