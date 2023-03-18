from typing import AsyncIterable

from .interface import ChannelAdapter, ChannelData, Content, PostUpdate


class Kaggle(ChannelAdapter):
    domain = 'kaggle.com'

    def track(self, url: str) -> ChannelData:
        return ChannelData(
            update_url='https://www.kaggle.com/competitions',
            name='Kaggle Competitions',
            url='https://www.kaggle.com/competitions'
        )

    async def update(self, update_url: str, name: str) -> AsyncIterable[PostUpdate]:
        # FIXME
        import kaggle.api

        for competition in kaggle.api.competitions_list():
            yield PostUpdate(
                id=str(competition.id), url=competition.url,
                content=Content(title=competition.title, description=competition.description)
            )

    async def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
