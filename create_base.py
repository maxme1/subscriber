from sqlalchemy_utils import database_exists, create_database

from subscriber.base import make_engine
from subscriber.models import *

engine = make_engine()
if not database_exists(engine.url):
    create_database(engine.url)
    Base.metadata.create_all(engine)

assert database_exists(engine.url)
