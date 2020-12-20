import json
import os
import random
from abc import ABC, abstractmethod

import requests
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import aiofiles

from chatbot.connections import VKConnection
from chatbot.exceptions import TooManyAttachments, InvalidAttachmentType
from homm3_core.creatures_hota import ARMY_NUMBER_CHOICES
from homm3_core.towns import TOWNS
from chatbot.settings import config
import aiohttp


# TODO handle few boxes on one screen
class AbstractConversation(ABC):
    """"""

    source = ''

    def __init__(self, user_id: int):
        self.user_id = user_id

    @abstractmethod
    def inquire_for_guard_number(self) -> None:
        """Inquiries user to send how many units protect the box"""

    @abstractmethod
    def inquire_for_town(self) -> None:
        """Inquiries user to send what the main town in the zone where the pandora box is located"""

    @abstractmethod
    def send_results(self, message) -> None:
        """Sends recognition results"""

    @abstractmethod
    def send(self, message, **kwargs) -> None:
        """Sends message to user"""

    @abstractmethod
    def parse_incoming_message(self, message) -> dict:
        """Parses message from chatbot provider to internal structure: {"text": "...", "screenshot": "..."}"""

    async def screenshot_received(self, screenshot_url) -> None:
        """Saves the screenshot in the media folder and sends it to the recognition app

        Args:
            screenshot_url: url of the picture to recognize

        Returns:

        """

        # TODO download image to media
        screenshot_path = config['media_root'] + '/' + screenshot_url.split('/')[-1]

        async with aiofiles.open(screenshot_path, 'wb') as handler:
            with aiohttp.request('GET', screenshot_url) as response:
                await handler.write(await response.read())
        # TODO [db] save image path (in media) to database
        # TODO send image to app.recognition

    def new_message_received(self, message) -> None:
        """Parses, validates and handles new incoming message"""

        try:
            parsed_message = self.parse_incoming_message(message)
        except TooManyAttachments:
            self.send(
                'Please, send only one screenshot. If you want to calculate many boxes on different screens, '
                'then send it separately'
            )
            return
        except InvalidAttachmentType:
            self.send('Please, attach a picture to your message')
            return
        self.handle_incoming_message(parsed_message)

    def handle_incoming_message(self, message: dict) -> None:
        """Moves the user through the conversation steps

        Args:
            message: parsed message from user
                text:
                screenshot: url to download the screenshot

        Returns:

        """

        if not self.data.get('status'):
            if 'screenshot' not in message or not message['screenshot']:
                self.send_help()
            else:
                self.data = update_cache(self.user_id, status='inquire_for_guard_number')
                self.screenshot_received(message['screenshot'])
                self.inquire_for_guard_number()
        elif message['text'] == 'Cancel':
            self.finish()
            self.send('Ok, if you want to start again just send us a picture!', remove_keyboard=True)
        elif self.data['status'] == 'inquire_for_guard_number':
            if message['text'] not in dict(ARMY_NUMBER_CHOICES).values():
                self.send('Sorry, the number of guards is incorrect')
                self.inquire_for_guard_number()
            else:
                self.data = update_cache(self.user_id, status='inquire_for_town', guard_number=message['text'])
                self.inquire_for_town()
        elif self.data['status'] == 'inquire_for_town':
            if message['text'] not in TOWNS:
                self.send('Sorry, the town is incorrect')
                self.inquire_for_town()
            else:
                self.data['town'] = message['text']
                results = calculate()
                # TODO send results to user
                self.send(str(self.data))
                self.finish()
        else:
            self.send_help()

    def send_help(self) -> None:
        """Sends a hint on how to use the chatbot"""
        self.send(
            'To use chatbot, please, send a screenshot contains Pandora\'s Box with guard and objects around it, then '
            'follow the instructions. Enjoy!', remove_keyboard=True)

    def finish(self):
        """Removes all unnecessary data"""
        if 'screenshot' in self.data:
            os.remove(self.data['screenshot'])
        cache.delete(self.user_id)


class VKConversation(AbstractConversation):
    source = 'vk'

    def parse_incoming_message(self, message):
        """Parses, validates and handles new incoming message"""

        screenshot = None

        if message['attachments']:
            if len(message['attachments']) > 1:
                raise TooManyAttachments
            elif 'photo' not in message['attachments'][0]:
                raise InvalidAttachmentType

            for size in message['attachments'][0]['photo']['sizes']:
                # type = x -- a proportional copy of the picture with max side 604px
                if size['type'] == 'x':
                    screenshot = size['url']
                    break

        return {
            'text': message.get('text', ''),
            'screenshot': screenshot
        }

    def inquire_for_guard_number(self) -> None:
        """Inquiries user to send how many units protect the box"""

        keyboard = VkKeyboard()
        for idx, (_, number) in enumerate(ARMY_NUMBER_CHOICES[:6]):
            if idx != 0 and idx % 2 == 0:
                keyboard.add_line()
            keyboard.add_button(label=number, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button(label='Cancel', color=VkKeyboardColor.NEGATIVE)
        self.send(message='Please, choose the number of guards from the below', keyboard=keyboard.get_keyboard())

    def inquire_for_town(self) -> None:
        """Inquiries user to send what the main town in the zone where the pandora box is located"""

        keyboard = VkKeyboard()
        for idx, town in enumerate(sorted(TOWNS)):
            if idx != 0 and idx % 3 == 0:
                keyboard.add_line()
            keyboard.add_button(label=town, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button(label='Cancel', color=VkKeyboardColor.NEGATIVE)
        self.send(message='Please, choose the town from the below', keyboard=keyboard.get_keyboard())

    def send_results(self, message):
        """Sends recognition results"""

        self.send(message=message, keyboard='{"buttons": [], "one_time": true}')

    def send(self, message, **kwargs):
        """Sends message to user"""

        if 'remove_keyboard' in kwargs:
            kwargs['keyboard'] = '{"buttons": [], "one_time": true}'

        VKConnection().messages.send(
            user_id=self.user_id,
            message=message,
            random_id=random.randint(1000000, 999999999),
            **kwargs
        )
