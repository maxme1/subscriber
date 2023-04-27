import contextlib
import os
from functools import cache

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


# TODO: refactor this
@cache
def make_engine():
    return create_engine('postgresql://' + os.environ['POSTGRES_URL'])


@cache
def session_maker():
    return sessionmaker(autocommit=False, autoflush=False, bind=make_engine())


@contextlib.contextmanager
def db():
    session = session_maker()()
    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def get_or_create(session: Session, model, defaults: dict | None = None, **kwargs):
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


Base = declarative_base()
