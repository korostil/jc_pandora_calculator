import json
import logging
import traceback

from aiohttp import web

from communications import VKConversation
from settings import config


async def vk_view(request):
    """Receives messages from VK API"""

    data = await request.json()

    message_type = data.get("type")
    group_id = data.get("group_id")

    if group_id != config["vk"]["group_id"]:
        raise web.HTTPInternalServerError(text="Incorrect VK group id!")

    if message_type == "confirmation":
        return web.Response(text=config["vk"]["confirmation"])
    else:
        if data.get("secret") != config["vk"]["secret"]:
            logging.error("Invalid secret key!")
            raise web.HTTPForbidden(text="Invalid secret key!")

        try:
            if message_type == "message_new":
                conversation = VKConversation(
                    user_id=data["object"]["message"]["from_id"]
                )
                conversation.new_message_received(data["object"]["message"])
        except (TypeError, KeyError):
            logging.error(
                "Received invalid data: " + json.dumps(data, ensure_ascii=False)
            )
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            return web.Response(text="ok")
