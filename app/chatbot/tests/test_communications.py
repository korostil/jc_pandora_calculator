import json
import os

import pytest

from chatbot import exceptions
from chatbot.communications import VKConversation
from chatbot.settings import config


async def test_screenshot_received():
    group_avatar = "https://sun9-30.userapi.com/impg/5TkuxkpfKvgpo_-FiznonstrYwd9J27xeQxy8w/lsxtWYEIQLU.jpg"
    user_id = 1
    conversation = VKConversation(user_id)

    await conversation.screenshot_received(group_avatar)

    assert os.path.exists(config["media_root"] + "/lsxtWYEIQLU.jpg") is True


@pytest.mark.parametrize("source", ["vk"])
@pytest.mark.parametrize(
    "screenshot,expected_state",
    [
        (None, None),
        ("photo-72495085_457312921", {"status": "inquire_for_guard_number"}),
    ],
)
def test_the_first_contact(source, screenshot, expected_state):
    user_id = 1
    if source == "vk":
        conversation = VKConversation(user_id)

        conversation.handle_incoming_message({"screenshot": screenshot})

        assert (
            json.loads(cache.get(user_id))
            if cache.get(user_id)
            else cache.get(user_id) == expected_state
        )


@pytest.mark.parametrize("source", ["vk"])
@pytest.mark.parametrize(
    "message,expected_state",
    [
        ("nonsense", {"status": "inquire_for_guard_number"}),
        (
            "Lots (20-49)",
            {"status": "inquire_for_town", "guard_number": "Lots (20-49)"},
        ),
    ],
)
def test_guard_inquiring(source, message, expected_state):
    cache.clear()
    user_id = 1
    cache.set(user_id, '{"status": "inquire_for_guard_number"}')
    if source == "vk":
        conversation = VKConversation(user_id)

        conversation.handle_incoming_message({"text": message})

        assert json.loads(cache.get(user_id)) == expected_state


@pytest.mark.parametrize("source", ["vk"])
@pytest.mark.parametrize(
    "message,expected_state",
    [
        ("nonsense", {"status": "inquire_for_town", "guard_number": "Lots (20-49)"}),
        ("Castle", None),
    ],
)
def test_town_inquiring(source, message, expected_state):
    user_id = 1
    cache.set(user_id, '{"status": "inquire_for_town", "guard_number": "Lots (20-49)"}')
    if source == "vk":
        conversation = VKConversation(user_id)

        conversation.handle_incoming_message({"text": message})

        assert (
            json.loads(cache.get(user_id))
            if cache.get(user_id)
            else cache.get(user_id) == expected_state
        )


@pytest.mark.parametrize("source", ["vk"])
@pytest.mark.parametrize(
    "message,expected,raised",
    [
        (
            {"text": "test", "attachments": []},
            {"text": "test", "screenshot": None},
            None,
        ),
        (
            {
                "attachments": [
                    {"photo": {"sizes": [{"type": "x", "url": "http://vk.com"}]}}
                ]
            },
            {"text": "", "screenshot": "http://vk.com"},
            None,
        ),
        (
            {
                "attachments": [
                    {"photo": {"sizes": [{"type": "x", "url": "http://vk.com"}]}},
                    {"video": {}},
                ]
            },
            {"text": "", "screenshot": "http://vk.com"},
            exceptions.TooManyAttachments,
        ),
        (
            {"attachments": [{"video": {}}]},
            {"text": "", "screenshot": "http://vk.com"},
            exceptions.InvalidAttachmentType,
        ),
    ],
)
def test_parsing_incoming_message(source, message, expected, raised):
    user_id = 1
    conversation = VKConversation(user_id)

    if raised:
        with pytest.raises(raised):
            parsed_message = conversation.parse_incoming_message(message)
            assert parsed_message == expected
    else:
        parsed_message = conversation.parse_incoming_message(message)
        assert parsed_message == expected


@pytest.mark.parametrize("source", ["vk"])
def test_finishing_state(source):
    user_id = 1
    screenshot_path = "/tmp/test.png"
    open(screenshot_path, "wb")
    cache.set(
        user_id,
        '{"status": "inquire_for_town", "guard_number": "Lots (20-49)", "screenshot": "/tmp/test.png"}',
    )
    if source == "vk":
        conversation = VKConversation(user_id)

        conversation.finish()

        assert cache.get(user_id) is None
        assert os.path.exists(screenshot_path) is False
