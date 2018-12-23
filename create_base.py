from all_subscriptions_bot.database import *

with DATABASE:
    DATABASE.create_tables([User, Channel, ChannelPost, UserChannels])
