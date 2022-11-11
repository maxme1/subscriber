from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, urlunparse, ParseResult

import requests
from lxml import html

from .base import Content, ChannelAdapter, ChannelData, PostUpdate
from ..utils import store_url


class SongKick(ChannelAdapter):
    domain = 'songkick.com'
    add_name = True

    def track(self, url: str) -> ChannelData:
        parsed = urlparse(url)
        parts = Path(parsed.path).parts[1:]
        if len(parts) < 2 or parts[0] != 'artists':
            print(parts)
            raise ValueError('This is not a valid artist link.')
        parts = parts[:2]

        url = urlunparse(ParseResult(parsed.scheme, parsed.netloc, str(Path(*parts)), '', '', ''))
        doc = html.fromstring(requests.get(url).content.decode('utf-8'))
        header, = doc.cssselect('.artist-header')
        name, = header.cssselect('h1')
        image, = header.cssselect('img.artist-profile-image')
        name = name.text.strip()

        image = image.attrib.get('src')
        if image.startswith(r'//'):
            image = f'https:{image}'
        else:
            image = f'https://www.songkick.com/{image}'
        image = store_url(image)

        calendar = urlunparse(ParseResult(parsed.scheme, parsed.netloc, str(Path(*parts, 'calendar')), '', '', ''))
        return ChannelData(update_url=calendar, name=name, image=image, url=url)

    def update(self, update_url: str, name: str) -> Iterable[PostUpdate]:
        doc = html.fromstring(requests.get(update_url).content.decode('utf-8'))
        summary = doc.cssselect('#calendar-summary')
        if not summary:
            return

        summary, = summary
        for element in reversed(summary.cssselect('li.event-listing')):
            link, = element.cssselect('a')
            time, = link.cssselect('time')
            details, = link.cssselect('.event-details')
            location, = details.cssselect('.primary-detail')
            venue, = details.cssselect('.secondary-detail')

            location, venue = location.text_content().strip(), venue.text_content().strip()
            time = time.attrib.get('datetime', '').strip()
            # text = ''.join((html.tostring(x, encoding='utf-8').decode() for x in text.getchildren()))
            suffix = link.attrib.get('href', '')
            assert suffix
            link = f'https://www.songkick.com/{suffix}#{name}'

            desc = venue
            if time:
                desc += ' at ' + time

            yield PostUpdate(id=suffix, url=link, content=Content(title=location, description=desc))

    def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
