from sqlalchemy_utils import database_exists, create_database

from subscriber.base import engine
from subscriber.models import *

if not database_exists(engine.url):
    create_database(engine.url)
    Base.metadata.create_all(engine)

assert database_exists(engine.url)
