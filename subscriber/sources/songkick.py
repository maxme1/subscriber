from pathlib import Path
from typing import AsyncIterable
from urllib.parse import ParseResult, urlparse, urlunparse

import aiohttp
from lxml import html

from ..utils import url_to_base64
from .interface import ChannelAdapter, ChannelData, Content, PostUpdate


class SongKick(ChannelAdapter):
    domain = 'songkick.com'
    add_name = True

    @staticmethod
    async def track(url: str) -> ChannelData:
        parsed = urlparse(url)
        parts = Path(parsed.path).parts[1:]
        if len(parts) < 2 or parts[0] != 'artists':
            raise ValueError('This is not a valid artist link.')
        parts = parts[:2]

        url = urlunparse(ParseResult(parsed.scheme, parsed.netloc, str(Path(*parts)), '', '', ''))

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                doc = html.fromstring(await response.text())

            header, = doc.cssselect('.artist-header')
            name, = header.cssselect('h1')
            image, = header.cssselect('img.artist-profile-image')
            name = name.text.strip()

            image = image.attrib.get('src')
            if image.startswith(r'//'):
                image = f'https:{image}'
            else:
                image = f'https://www.songkick.com/{image}'
            image = await url_to_base64(image, session)

            calendar = urlunparse(ParseResult(parsed.scheme, parsed.netloc, str(Path(*parts, 'calendar')), '', '', ''))
            return ChannelData(update_url=calendar, name=name, image=image, url=url)

    async def update(self, update_url: str, name: str) -> AsyncIterable[PostUpdate]:
        async with aiohttp.ClientSession() as session:
            async with session.get(update_url) as response:
                doc = html.fromstring(await response.text())

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

    async def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
