import base64
import os
import re
import tempfile
from functools import cache
from pathlib import Path
from typing import Union

import aiohttp
import lxml.html
from tarn import Disk, Storage

URL_PATTERN = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$',
    flags=re.IGNORECASE
)


@cache
def build_storage():
    return Storage(Disk(os.environ['STORAGE_PATH']))


def drop_prefix(x, prefix):
    assert x.startswith(prefix), x
    return x[len(prefix):]


def get_og_tags(html: Union[str, bytes]):
    res = {}
    doc = lxml.html.fromstring(html)
    for meta in doc.cssselect('meta'):
        attrs = meta.attrib
        if set(attrs) >= {'property', 'content'} and attrs['property'].startswith('og:'):
            res[attrs['property'][3:]] = attrs['content']

    return res


def file_to_base64(path):
    with open(path, 'rb') as fd:
        return base64.b64encode(fd.read())


def store_base64(encoded):
    with tempfile.TemporaryDirectory() as folder:
        file = Path(folder, 'file')

        with open(file, 'wb') as fd:
            fd.write(base64.b64decode(encoded))

        return build_storage().write(file)


def storage_resolve(key):
    return build_storage().resolve(key)


async def url_to_base64(url: str, session: aiohttp.ClientSession):
    if url is None:
        return

    async with session.get(url) as response:
        return base64.b64encode(await response.read())
