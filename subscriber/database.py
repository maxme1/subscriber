import logging
from datetime import datetime

import feedparser
import requests
from lxml import html
from opengraph.opengraph import OpenGraph
from peewee import *

logger = logging.getLogger(__name__)

DATABASE_PATH = 'db.sqlite3'
DATABASE = SqliteDatabase(DATABASE_PATH, pragmas=[('journal_mode', 'wal')])
atomic = DATABASE.atomic

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en,en-US;q=0.7,ru;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
}


class Channel(Model):
    TYPES = ['youtube', 'vk', 'twitter']

    update_url = CharField(max_length=1000, unique=True)
    channel_url = CharField(max_length=1000, unique=True)
    name = CharField(max_length=200)
    last_updated = DateTimeField(default=datetime.now)
    type = CharField(choices=tuple(enumerate(TYPES)))

    class Meta:
        database = DATABASE

    def __str__(self):
        return f'{self.name} - {self.type}'

    @atomic()
    def trigger_update(self, created=None):
        self.last_updated = datetime.now()
        self.save()
        logger.debug('Updating channel %s', self)

        updater = getattr(self, '_update_' + self.type)
        for i, url in updater():
            if ChannelPost.select().where(ChannelPost.identifier == i, ChannelPost.channel == self):
                continue

            fields = OpenGraph(url, scrape=True)
            post = ChannelPost(
                identifier=i, url=url, channel=self,
                title=fields.get('title', ''), image=fields.get('image', ''),
                description=fields.get('description', '')
            )
            if created is not None:
                post.created = created
            post.save()
            logger.debug('New post %s for %s', url, self)

    def _update_youtube(self):
        for post in reversed(feedparser.parse(self.update_url)['entries']):
            url = post['link']
            yield post['id'], url

    def _update_vk(self):
        doc = html.fromstring(requests.get(self.update_url, headers=REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                url = f'https://vk.com/wall-{i}'
                yield i, url

    def _update_twitter(self):
        return
        doc = html.fromstring(requests.get(self.update_url, headers=REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.tweet')):
            link = element.attrib["data-permalink-path"]
            yield ChannelPost(identifier=link, url=f'https://twitter.com{link}', channel=self)


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
