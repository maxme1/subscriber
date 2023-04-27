import pytest
from aiohttp import ClientSession

from subscriber.sources import Twitter, ChannelData, PostUpdate, Content


@pytest.mark.asyncio
async def test_track():
    url = 'https://twitter.com/jack'
    jack = await Twitter().track(url)
    assert jack == ChannelData(update_url=url, name='jack')


@pytest.mark.asyncio
async def test_update():
    async with ClientSession() as session:
        first = [x async for x in Twitter().update('https://twitter.com/jack', 'jack', session)][0]
    link = 'https://nitter.cz/jack/status/20#m'
    assert first == PostUpdate(id=link, url=link, content=Content(
        description='RT by @jack: just setting up my twttr'
    ))
