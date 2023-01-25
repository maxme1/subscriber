from typing import Iterable

import kaggle.api

from .base import Content, ChannelAdapter, ChannelData, PostUpdate


class GrandChallenge(ChannelAdapter):
    domain = 'kaggle.com'

    def track(self, url: str) -> ChannelData:
        return ChannelData(
            update_url='https://www.kaggle.com/competitions',
            name='Kaggle Competitions',
            url='https://www.kaggle.com/competitions'
        )

    def update(self, update_url: str, name: str) -> Iterable[PostUpdate]:
        for competition in kaggle.api.competitions_list():
            yield PostUpdate(
                id=str(competition.id), url=competition.url,
                content=Content(title=competition.title, description=competition.description)
            )

    def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
