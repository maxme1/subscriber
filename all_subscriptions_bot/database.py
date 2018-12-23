from datetime import datetime

from peewee import *

DATABASE = SqliteDatabase('db.sqlite3')
DEFAULT_DATE = datetime(year=2000, month=1, day=1)


class Channel(Model):
    TYPES = ['YouTube']

    name = CharField()
    url = CharField(max_length=1000, unique=True)
    last_updated = DateTimeField(default=DEFAULT_DATE)
    type = CharField(choices=tuple(enumerate(TYPES)))

    class Meta:
        database = DATABASE

    def __str__(self):
        return self.name


class User(Model):
    identifier = CharField(unique=True)
    channels = ManyToManyField(Channel, backref='users')
    last_updated = DateTimeField(default=DEFAULT_DATE)

    class Meta:
        database = DATABASE

    def __str__(self):
        return self.identifier


UserChannels = User.channels.get_through_model()


class ChannelPost(Model):
    identifier = CharField()
    title = CharField()
    url = CharField()

    image_url = CharField(null=True)
    description = TextField(null=True)

    channel = ForeignKeyField(Channel)
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = DATABASE


def atomic(func):
    def wrapper(*args, **kwargs):
        with DATABASE.atomic():
            return func(*args, **kwargs)

    return wrapper
