import json

from celery import Celery

from .channels import ChannelAdapter
from .channels.base import ChannelData, Content
from .utils import with_session

app = Celery('subscriber', broker='redis://redis', backend='redis://redis')


@app.task
@with_session
def update(session):
    from .crud import update_base

    update_base(session)


@app.task
def delayed(kind: str, method: str, *args):
    adapter = ChannelAdapter.dispatch_type(kind)
    method = getattr(adapter, method)

    value = method(*args)
    if isinstance(value, (ChannelData, Content)):
        return json.loads(value.json())
    if not isinstance(value, list):
        value = list(value)

    return [json.loads(x.json()) for x in value]
