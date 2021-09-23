import logging
from datetime import datetime

from peewee import *

logger = logging.getLogger(__name__)

DATABASE_PATH = '/db/db.sqlite3'
DATABASE = SqliteDatabase(DATABASE_PATH, pragmas=[('journal_mode', 'wal')])
atomic = DATABASE.atomic


class Channel(Model):
    update_url = CharField(max_length=1000, unique=True)
    channel_url = CharField(max_length=1000, unique=True)
    name = CharField(max_length=200)
    image = CharField(default='')

    last_updated = DateTimeField(default=datetime.now)
    type = CharField()

    class Meta:
        database = DATABASE

    def __str__(self):
        return f'{self.name} - {self.type}'


class User(Model):
    identifier = CharField(unique=True)
    channels = ManyToManyField(Channel, backref='users')
    last_updated = DateTimeField(default=datetime.now)

    class Meta:
        database = DATABASE

    def __str__(self):
        return self.identifier


UserChannels = User.channels.get_through_model()


class ChannelPost(Model):
    identifier = CharField()
    url = CharField(unique=True)
    title = CharField(default='')
    image = CharField(default='')
    description = TextField(default='')

    channel = ForeignKeyField(Channel)
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = DATABASE
        indexes = (('identifier', 'channel_id'), True),


class Task(Model):
    """
    Used to delete the `message` from `chat` after a deadline.
    """
    chat = IntegerField()
    message = IntegerField()
    when = DateTimeField()

    class Meta:
        database = DATABASE
