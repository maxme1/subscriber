from functools import cache

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# TODO: refactor this
@cache
def make_engine():
    return create_engine('postgresql://postgres:postgres@db:5432/subscriber')


@cache
def session_maker():
    return sessionmaker(autocommit=False, autoflush=False, bind=make_engine())


@cache
def SessionLocal():
    return session_maker()()


Base = declarative_base()
