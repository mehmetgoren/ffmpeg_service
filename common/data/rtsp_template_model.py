import shortuuid


class RtspTemplateModel:
    def __init__(self):
        self.id: str = shortuuid.uuid()[:11]
        self.name: str = ''
        self.description: str = ''
        self.brand: str = ''
        self.default_user: str = ''
        self.default_password: str = ''
        self.default_port: str = ''
        self.address: str = ''
        self.route: str = ''
        self.templates: str = '{user},{password},{ip},{port},{route}'
