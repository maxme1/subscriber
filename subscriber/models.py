import enum

from pydantic import BaseModel, Extra
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Unicode, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .base import Base


class NoExtra(BaseModel):
    class Config:
        extra = Extra.forbid


Identifier = str


class FileTable(Base):
    __tablename__ = 'File'
    id = Column(Integer, primary_key=True)

    # internal id
    internal = Column(Unicode(64), nullable=False, unique=True)
    # ids for different destinations
    telegram = Column(Unicode, nullable=True, unique=True)


class File(NoExtra):
    internal: Identifier
    telegram: Identifier | None


class SourceTable(Base):
    __tablename__ = 'Source'
    id = Column(Integer, primary_key=True)

    url = Column(Unicode(1000), nullable=False, unique=True)
    update_url = Column(Unicode(1000), nullable=False, unique=True)
    name = Column(Unicode(1000), nullable=False)
    image_id = Column(ForeignKey(FileTable.id), nullable=True)
    image = relationship(FileTable)

    chats = relationship('ChatTable', secondary='ChatToSource', back_populates='sources')
    posts = relationship('PostTable', back_populates='source')

    # internal
    type = Column(Unicode, nullable=False)

    def __str__(self):
        return f'{self.name} - {self.type}'


class Source(BaseModel):
    pk: int
    name: str
    type: str
    update_url: str


class ChatTable(Base):
    __tablename__ = 'Chat'
    id = Column(Integer, primary_key=True)

    identifier = Column(Unicode, nullable=False, unique=True)
    type = Column(Unicode, nullable=False)

    sources = relationship('SourceTable', secondary='ChatToSource', back_populates='chats')
    chat_posts = relationship('ChatPost', back_populates='chat')

    # posts = relationship('Post', secondary='ChatPost', back_populates='chats')

    def __str__(self):
        return self.identifier


class PostTable(Base):
    __tablename__ = 'Post'
    __table_args__ = UniqueConstraint('identifier', 'source_id'),
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False, server_default=func.now())

    identifier = Column(Unicode, nullable=False)
    url = Column(Unicode, nullable=False)
    title = Column(Unicode, nullable=True)
    description = Column(Unicode, nullable=True)
    image_id = Column(ForeignKey(FileTable.id), nullable=True)
    image = relationship(FileTable)

    source_id = Column(ForeignKey(SourceTable.id, ondelete='CASCADE'), nullable=False)
    source = relationship(SourceTable, back_populates='posts')

    chat_posts = relationship('ChatPost', back_populates='post')


class Post(BaseModel):
    title: str
    description: str
    url: str
    image: File | None


# secondary

class ChatToSource(Base):
    __tablename__ = 'ChatToSource'
    __table_args__ = UniqueConstraint('chat_id', 'source_id'),
    id = Column(Integer, primary_key=True)

    chat_id = Column(ForeignKey(ChatTable.id, ondelete='CASCADE'), nullable=False)
    chat = relationship(ChatTable, viewonly=True)
    source_id = Column(ForeignKey(SourceTable.id, ondelete='CASCADE'), nullable=False)
    source = relationship(SourceTable, viewonly=True)


class ChatPostState(enum.Enum):
    Pending, Posted, Keeping, Deleted = range(4)


class ChatPost(Base):
    __tablename__ = 'ChatPost'
    __table_args__ = UniqueConstraint('chat_id', 'post_id'),
    id = Column(Integer, primary_key=True)

    state = Column(Enum(ChatPostState), nullable=False)
    created = Column(DateTime, nullable=False, server_default=func.now())

    message_id = Column(Unicode, nullable=False)
    chat_id = Column(ForeignKey(ChatTable.id, ondelete='CASCADE'), nullable=False)
    chat = relationship(ChatTable, back_populates='chat_posts')
    post_id = Column(ForeignKey(PostTable.id, ondelete='CASCADE'), nullable=False)
    post = relationship(PostTable, back_populates='chat_posts')
