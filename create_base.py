import os

from subscriber.base import *
from subscriber.models import *

assert not os.path.exists(DATABASE_PATH)
Base.metadata.create_all(engine)
