import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum


class MessageType(enum.Enum):
    incoming = False
    outgoing = True


Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64))
    last_name = Column(String(64))

    @property
    def status(self):
        return

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"


class VKUser(User):
    __tablename__ = "vk_user"

    def __repr__(self):
        return f"User<id='{self.id}', name='{self.fullname}'>"


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    type = Column(Enum(MessageType))
    text = Column(String)
    sent = Column(DateTime)

    user = relationship("User", back_populates="messages")
    request = relationship("UserRequest")

    def __repr__(self):
        return f"Message<id='{self.id}', user='{self.user}', sent='{self.sent}'>"


class UserRequest(Base):
    __tablename__ = "user_request"

    id = Column(Integer, primary_key=True)
    image = Column(String(64))
    town = Column(String(64))  # TODO choice
    guard = Column(String(64))  # TODO choice
    guard_number = Column(String(64))  # TODO choice
    objects = Column(String)
    result = Column(String)

    user = relationship("User")

    def __repr__(self):
        return f"UserRequest<id='{self.id}', user='{self.user.fullname}'>"
