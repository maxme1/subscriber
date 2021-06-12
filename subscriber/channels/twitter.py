import re
from typing import Iterable
from urllib.parse import urlparse
import time

from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options

from .base import Content, ChannelAdapter, ChannelData, PostUpdate


class Twitter(ChannelAdapter):
    domain = 'twitter.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)

    def track(self, url: str) -> ChannelData:
        path = urlparse(url).path
        name = Twitter.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        return ChannelData(url, name.group(1))

    def update(self, url: str) -> Iterable[PostUpdate]:
        options = Options()
        profile = FirefoxProfile()
        profile.set_preference('permissions.default.image', 2)
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        options.headless = True
        driver = webdriver.Firefox(firefox_options=options, firefox_profile=profile)
        try:
            driver.get(url)
            tweets = self._get_tweets(driver)

            # wait up to 2 seconds
            n_iters = 20
            while not tweets and n_iters > 0:
                time.sleep(0.1)
                tweets = self._get_tweets(driver)
                n_iters -= 1

            results = []
            for tweet in tweets:
                content = self._find_text(tweet)
                for link in tweet.find_elements_by_css_selector('a[role=link]'):
                    link = link.get_property('href')
                    if '/status/' in link:
                        results.append(PostUpdate(link, f'https://twitter.com{link}', content))
                        break

            return reversed(results)

        finally:
            driver.close()

    def scrape(self, url: str) -> Content:
        raise RuntimeError

    @staticmethod
    def _get_tweets(driver):
        tweets = driver.find_elements_by_css_selector('[data-testid=tweet]')
        if tweets:
            driver.execute_script("window.stop();")
            tweets = driver.find_elements_by_css_selector('[data-testid=tweet]')
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
