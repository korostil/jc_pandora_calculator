class TooManyAttachments(Exception):
    """Too many attachments in the message"""


class InvalidAttachmentType(Exception):
    """An image file was expected, but a different type of file was attached to the message"""
