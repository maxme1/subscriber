import asyncio
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AsyncIterable
from urllib.parse import urlparse

from aiohttp import ClientSession
from jboc import collect
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement

from ..utils import file_to_base64
from .interface import ChannelData, Content, DomainMatch, PostUpdate


class Twitter(DomainMatch):
    domain = 'twitter.com'
    queue = 'selenium'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    TWEET = re.compile(r'^.*/status/\d+$')

    def __init__(self):
        self._pool = ThreadPoolExecutor(1)
        options = Options()
        options.headless = True
        profile = FirefoxProfile()
        # don't load images
        # profile.set_preference('permissions.default.image', 2)
        # don't use flash
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        self._driver = webdriver.Firefox(firefox_options=options, firefox_profile=profile)
        self._driver.set_window_size(1000, 1000)

    def __del__(self):
        self._driver.close()
        self._pool.shutdown(wait=True)

    @staticmethod
    async def track(url: str) -> ChannelData:
        path = urlparse(url).path
        name = Twitter.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        return ChannelData(update_url=url, name=name.group(1))

    async def update(self, update_url: str, name: str, session: ClientSession) -> AsyncIterable[PostUpdate]:
        results = await asyncio.wrap_future(self._pool.submit(self._update, update_url))
        for result in results:
            yield result

    @collect
    def _update(self, update_url: str):
        self._driver.get(update_url)

        try:
            tweets = self._get_tweets()

            # wait up to 2 seconds
            n_iters = 20
            while not tweets and n_iters > 0:
                time.sleep(0.1)
                tweets = self._get_tweets()
                n_iters -= 1

            # disable an annoying message
            self._driver.execute_script(
                "arguments[0].style.visibility='hidden'", self._driver.find_element_by_id('layers')
            )

            tweet: WebElement
            with tempfile.TemporaryDirectory() as folder:
                file = str(Path(folder, 'file.png'))

                for tweet in reversed(tweets):
                    # content = self._find_text(tweet)
                    for link in tweet.find_elements_by_css_selector('a[role=link]'):
                        link = link.get_property('href')

                        if self.TWEET.match(link):
                            # take a tweet screenshot
                            if not link.startswith('https://twitter.com'):
                                link = 'https://twitter.com' + link
                            tweet.screenshot(file)
                            yield PostUpdate(
                                id=link, url=link,
                                content=Content(image=file_to_base64(file)),
                            )
                            break

        except StaleElementReferenceException:
            pass

    async def scrape(self, post_url: str, session: ClientSession) -> Content:
        raise RuntimeError

    def _get_tweets(self):
        tweets = self._driver.find_elements_by_css_selector('[data-testid=tweet]')
        if tweets:
            self._driver.execute_script('window.stop();')
            tweets = self._driver.find_elements_by_css_selector('[data-testid=tweet]')
            assert tweets
        return tweets

    @staticmethod
    def _find_text(tweet):
        for lang in tweet.find_elements_by_css_selector('[lang]'):
            for span in lang.find_elements_by_css_selector('span'):
                text = span.text
                if text:
                    return Content(description=text)

        return Content()
