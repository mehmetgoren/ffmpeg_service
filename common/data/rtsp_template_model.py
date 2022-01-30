import shortuuid


class RtspTemplateModel:
    def __init__(self):
        self.id = shortuuid.uuid()[:11]
        self.name = ''
        self.description = ''
        self.brand = ''
        self.default_user = ''
        self.default_password = ''
        self.default_port = ''
        self.address = ''
        self.route = ''
        self.templates = '{user},{password},{ip},{port},{route}'

    def map_from(self, fixed_dic: dict):
        self.__dict__.update(fixed_dic)
        return self
