import pytest

from chatbot.communications import VKConversation, AbstractConversation


def blank_func(*args, **kwargs):
    pass


@pytest.fixture(autouse=True)
def mock_vk_message(monkeypatch):
    monkeypatch.setattr(VKConversation, 'send', blank_func)


@pytest.fixture(autouse=True)
def mock_screenshot_save(monkeypatch):
    monkeypatch.setattr(AbstractConversation, 'screenshot_received', blank_func)
