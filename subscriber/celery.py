import json

from celery import Celery

from .channels import ChannelAdapter
from .utils import with_session

app = Celery('subscriber', broker='redis://redis', backend='redis://redis')


@app.task
@with_session
def update(session):
    from .crud import update_base

    update_base(session)


@app.task
def delayed(kind: str, method_name: str, *args):
    adapter = ChannelAdapter.dispatch_type(kind)
    method = getattr(adapter, method_name)

    value = method(*args)
    if method_name == 'update':
        return [json.loads(x.json()) for x in value]

    return json.loads(value.json())
