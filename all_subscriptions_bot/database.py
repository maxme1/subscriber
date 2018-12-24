from datetime import datetime

import feedparser
from peewee import *

DATABASE_PATH = 'db.sqlite3'
DATABASE = SqliteDatabase(DATABASE_PATH)


def atomic(func):
    def wrapper(*args, **kwargs):
        with DATABASE.atomic():
            return func(*args, **kwargs)

    return wrapper


class Channel(Model):
    TYPES = ['YouTube']

    name = CharField()
    url = CharField(max_length=1000, unique=True)
    last_updated = DateTimeField(default=datetime.now)
    type = CharField(choices=tuple(enumerate(TYPES)))

    class Meta:
        database = DATABASE

    def __str__(self):
        return self.name

    @atomic
    def trigger_update(self):
        updater = getattr(self, '_update_' + self.type.lower())
        updater()

    def _update_youtube(self):
        self.last_updated = datetime.now()
        self.save()

        for post in feedparser.parse(self.url)['entries']:
            try:
                ChannelPost(
                    identifier=post['id'], title=post['title'], url=post['link'],
                    image_url=post['media_thumbnail'][0]['url'], description=post['summary'],
                    channel=self
                ).save()
            except IntegrityError:
                pass


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
    identifier = CharField(unique=True)
    url = CharField()
    # title = CharField()
    # image_url = CharField(null=True)
    # description = TextField(null=True)

    channel = ForeignKeyField(Channel)
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = DATABASE
