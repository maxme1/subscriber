import enum

from sqlalchemy import Column, ForeignKey, Integer, Unicode, DateTime, func, UniqueConstraint, Enum
from sqlalchemy.orm import relationship

from .base import Base


class TelegramFile(Base):
    __tablename__ = 'TelegramFile'
    id = Column(Integer, primary_key=True)

    hash = Column(Unicode(64), nullable=False, unique=True)
    identifier = Column(Unicode, nullable=True, unique=True)


class Channel(Base):
    __tablename__ = 'Channel'
    id = Column(Integer, primary_key=True)

    update_url = Column(Unicode(1000), nullable=False, unique=True)
    channel_url = Column(Unicode(1000), nullable=False, unique=True)
    name = Column(Unicode(1000), nullable=False)
    image_id = Column(ForeignKey(TelegramFile.id), nullable=True)
    image = relationship(TelegramFile)

    chats = relationship('Chat', secondary='ChatChannel', back_populates='channels')
    posts = relationship('Post', back_populates='channel')

    # internal
    type = Column(Unicode, nullable=False)

    def __str__(self):
        return f'{self.name} - {self.type}'


class Chat(Base):
    __tablename__ = 'Chat'
    id = Column(Integer, primary_key=True)

    identifier = Column(Unicode, nullable=False, unique=True)

    channels = relationship('Channel', secondary='ChatChannel', back_populates='chats')
    posts = relationship('Post', secondary='ChatPost', back_populates='chats')

    def __str__(self):
        return self.identifier


class Post(Base):
    __tablename__ = 'Post'
    __table_args__ = UniqueConstraint('identifier', 'channel_id'),
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())

    identifier = Column(Unicode, nullable=False)
    url = Column(Unicode, nullable=False)
    title = Column(Unicode, nullable=True)
    description = Column(Unicode, nullable=True)
    image_id = Column(ForeignKey(TelegramFile.id), nullable=True)
    image = relationship(TelegramFile)

    channel_id = Column(ForeignKey(Channel.id, ondelete='CASCADE'), nullable=False)
    channel = relationship(Channel, back_populates='posts')

    chats = relationship(Chat, secondary='ChatPost', back_populates='posts')


# secondary

class ChatChannel(Base):
    __tablename__ = 'ChatChannel'
    __table_args__ = UniqueConstraint('chat_id', 'channel_id'),
    id = Column(Integer, primary_key=True)

    chat_id = Column(ForeignKey(Chat.id, ondelete='CASCADE'), nullable=False)
    # chat = relationship(Chat)
    channel_id = Column(ForeignKey(Channel.id, ondelete='CASCADE'), nullable=False)
    # channel = relationship(Channel)


class ChatPostState(enum.Enum):
    Pending, Posted, Keeping, Deleted = range(4)


class ChatPost(Base):
    __tablename__ = 'ChatPost'
    __table_args__ = UniqueConstraint('chat_id', 'post_id'),
    id = Column(Integer, primary_key=True)

    state = Column(Enum(ChatPostState), nullable=False)
    message_id = Column(Unicode, nullable=True)

    chat_id = Column(ForeignKey(Chat.id, ondelete='CASCADE'), nullable=False)
    # chat = relationship(Chat)
    post_id = Column(ForeignKey(Post.id, ondelete='CASCADE'), nullable=False)
    # post = relationship(Post)
