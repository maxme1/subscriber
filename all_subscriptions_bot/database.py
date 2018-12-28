from datetime import datetime

import feedparser
import requests
from lxml import html
from peewee import *

DATABASE_PATH = 'db.sqlite3'
DATABASE = SqliteDatabase(DATABASE_PATH, pragmas=[('journal_mode', 'wal')])
REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 '
                                 '(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def atomic(func):
    def wrapper(*args, **kwargs):
        with DATABASE.atomic():
            return func(*args, **kwargs)

    return wrapper


class Channel(Model):
    TYPES = ['youtube', 'vk']

    # TODO: channel url is not always request url
    url = CharField(max_length=1000, unique=True)
    last_updated = DateTimeField(default=datetime.now)
    type = CharField(choices=tuple(enumerate(TYPES)))

    class Meta:
        database = DATABASE

    def __str__(self):
        return self.name

    @atomic
    def trigger_update(self, created=None):
        self.last_updated = datetime.now()
        self.save()

        updater = getattr(self, '_update_' + self.type)
        for post in updater():
            try:
                if created is not None:
                    post.created = created
                post.save()
            except IntegrityError:
                pass

    def _update_youtube(self):
        for post in reversed(feedparser.parse(self.url)['entries']):
            yield ChannelPost(identifier=post['id'], url=post['link'], channel=self)

    def _update_vk(self):
        doc = html.fromstring(requests.get(self.url, headers=REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                yield ChannelPost(identifier=i, url=f'https://vk.com/wall-{i}', channel=self)


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

    channel = ForeignKeyField(Channel)
    created = DateTimeField(default=datetime.now)

    class Meta:
        database = DATABASE
        indexes = (('identifier', 'channel_id'), True),
