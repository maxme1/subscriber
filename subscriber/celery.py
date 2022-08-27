from celery import Celery

from .crud import update_base
from .utils import with_session

app = Celery('subscriber', broker='redis://redis')


@app.task
@with_session
def update(session):
    update_base(session)
