import os

from subscriber.database import *

if os.path.exists(DATABASE_PATH):
    os.remove(DATABASE_PATH)

with DATABASE:
    DATABASE.create_tables([User, Channel, ChannelPost, UserChannels])
