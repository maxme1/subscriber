import hashlib
import json
import logging
import os
from pathlib import Path

from celery import Celery

from .channels import ChannelAdapter
from .utils import OutdatedCode

logger = logging.getLogger(__name__)

broker = 'redis://' + os.environ['REDIS']
app = Celery('subscriber', broker=broker, backend=broker)
_hasher = hashlib.sha256()
for _file in sorted(Path(__file__).resolve().parent.parent.glob('**/*.py')):
    with open(_file, 'rb') as _fd:
        _hasher.update(_fd.read())

CODE_HASH: str = _hasher.hexdigest()


# @app.task
# @with_session
# def update(session):
#     from .crud import update_base
#
#     update_base(session)


@app.task
def delayed(code_hash: str, kind: str, method_name: str, *args):
    if code_hash != CODE_HASH:
        logger.critical('You version of the worker is outdated. Please upgrade')
        raise OutdatedCode(CODE_HASH)

    adapter = ChannelAdapter.dispatch_type(kind)
    method = getattr(adapter, method_name)

    value = method(*args)
    if method_name == 'update':
        return CODE_HASH, [json.loads(x.json()) for x in value]

    return CODE_HASH, json.loads(value.json())
