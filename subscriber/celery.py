import json
from contextlib import suppress

from celery import Celery
from celery.result import AsyncResult
from pydantic import ValidationError

from .channels import ChannelAdapter
from .channels.base import ChannelData, Content, PostUpdate
from .crud import update_base
from .utils import with_session

app = Celery('subscriber', broker='redis://redis', backend='redis://redis')


@app.task
@with_session
def update(session):
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


def call_adapter_method(kind: str, method, *args):
    if not isinstance(method, str):
        method = method.__name__

    # result: AsyncResult = delayed(kind, method, *args).delay()
    # value = result.get()
    value = delayed(kind, method, *args)

    with suppress(ValidationError):
        return ChannelData.parse_obj(value)
    with suppress(ValidationError):
        return Content.parse_obj(value)
    return list(map(PostUpdate.parse_obj, value))
