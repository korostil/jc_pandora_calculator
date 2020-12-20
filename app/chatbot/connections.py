import vk_api

from chatbot.settings import config


class VKConnection:
    """Connection to VK group"""

    instance = None

    def __new__(cls):
        if not cls.instance:
            cls.renew()
        return cls.instance

    @classmethod
    def renew(cls):
        cls.instance = vk_api.VkApi(token=config['vk']['group_token'], api_version='5.103').get_api()
