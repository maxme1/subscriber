import pytest
from aiohttp import ClientSession

from subscriber.sources import Twitter, ChannelData, PostUpdate, Content


@pytest.mark.asyncio
async def test_track():
    url = 'https://twitter.com/jack'
    jack = await Twitter().track(url)
    assert jack == ChannelData(update_url=url, name='jack')


@pytest.mark.skip('Nitter was shut down')
@pytest.mark.asyncio
async def test_update():
    async with ClientSession() as session:
        first = [x async for x in Twitter().update('https://twitter.com/jack', 'jack', session)][0]
    assert first == PostUpdate(id='jack/status/20', url='https://nitter.cz/jack/status/20#m', content=Content(
        description='RT by @jack: just setting up my twttr'
    ))
