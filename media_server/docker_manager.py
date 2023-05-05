from typing import List, Any
import docker
from redis.client import Redis

from stream.stream_model import StreamModel, MediaServerType
from media_server.media_server_models import BaseMediaServerModel, Go2RtcMediaServerModel, SrsRealtimeMediaServerModel, LiveGoMediaServerModel, \
    NodeMediaServerModel


# for more info: https://docker-py.readthedocs.io/en/stable/containers.html
class DockerManager:
    def __init__(self, connection: Redis):
        self.connection: Redis = connection
        self.client = docker.from_env()

    def __create_media_server_model(self, ms_type: MediaServerType, stream_id: str) -> BaseMediaServerModel:
        if ms_type == MediaServerType.GO_2_RTC:
            ms_model = Go2RtcMediaServerModel(stream_id, self.connection)
        elif ms_type == MediaServerType.SRS:
            ms_model = SrsRealtimeMediaServerModel(stream_id, self.connection)
        elif ms_type == MediaServerType.LIVE_GO:
            ms_model = LiveGoMediaServerModel(stream_id, self.connection)
        elif ms_type == MediaServerType.NODE_MEDIA_SERVER:
            ms_model = NodeMediaServerModel(stream_id, self.connection)
        else:
            raise NotImplementedError('MediaServerType was not match')

        ms_model.int_ports()

        return ms_model

    def __init_container(self, ms_model: BaseMediaServerModel, all_containers: List):
        container_name = ms_model.get_container_name()
        for container in all_containers:
            if container.name == container_name:
                self.stop_container(container)
                break
        container = self.client.containers.run(ms_model.get_image_name(), detach=True,
                                               command=ms_model.get_commands(),
                                               # auto_remove=True, remove=True,
                                               restart_policy={'Name': 'unless-stopped'},
                                               name=container_name,
                                               ports=ms_model.get_ports())
        return container

    def run(self, ms_type: MediaServerType, stream_id: str) -> (BaseMediaServerModel, Any):
        ms_model = self.__create_media_server_model(ms_type, stream_id)
        all_containers = self.client.containers.list(all=True)
        container = self.__init_container(ms_model, all_containers)
        return ms_model, container

    def remove(self, model: StreamModel):
        container = self.get_container(model)
        if container is not None:
            self.stop_container(container)

    def get_container_by(self, container_name):
        filters: dict = {'name': container_name}
        containers = self.client.containers.list(filters=filters)
        return containers[0] if len(containers) > 0 else None

    def get_container(self, model: StreamModel):
        container_name = model.ms_container_name
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
    def parse_image_name(container) -> str:
        tags = container.image.tags
        return tags[0].replace(':latest', '') if len(tags) > 0 else ''
