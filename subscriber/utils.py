import contextlib
import functools
import os
import re
import tempfile
from pathlib import Path
from typing import Union
from urllib.request import urlretrieve

import lxml.html
from tarn import Storage, Disk
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session

from subscriber.base import SessionLocal

URL_PATTERN = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$',
    flags=re.IGNORECASE
)
STORAGE = Storage(Disk(os.environ['STORAGE_PATH']))


def drop_prefix(x, prefix):
    assert x.startswith(prefix), x
    return x[len(prefix):]


def get_or_create(session: Session, model, defaults: dict = None, **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), False
    except NoResultFound:
        kwargs.update(defaults or {})
        try:
            with session.begin_nested():
                created = model(**kwargs)
                session.add(created)
                session.flush()
                return created, True

        except IntegrityError:
            return session.query(model).filter_by(**kwargs).one(), False


def get_og_tags(html: Union[str, bytes]):
    res = {}
    doc = lxml.html.fromstring(html)
    for meta in doc.cssselect('meta'):
        attrs = meta.attrib
        if set(attrs) >= {'property', 'content'} and attrs['property'].startswith('og:'):
            res[attrs['property'][3:]] = attrs['content']

    return res


def store_url(url: str):
    if url is None:
        return

    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp, 'file')
        urlretrieve(url, file)
        return STORAGE.write(file)


def no_context(func):
    return lambda update, context: func(update)


def with_session(func):
    @functools.wraps(func)
    @contextlib.contextmanager
    def wrapper(*args):
        session = SessionLocal()
        try:
            value = func(*args, session)
            session.commit()
            return value

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    return wrapper
