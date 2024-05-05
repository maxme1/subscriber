A Telegram bot that keeps all your subscriptions in one place

It can notify you about:

- new videos in [YouTube](https://www.youtube.com/) channels
- new posts in [Twitter](https://twitter.com/) feeds
- new concerts for artists and bands from [SongKick](https://songkick.com/)
- new posts from [VK](https://vk.com/) public channels
- new [Kaggle](https://www.kaggle.com/) competitions
- new [GrandChallenge](https://grand-challenge.org/) competitions
- new entries in any RSS feed

Just send it a link to a channel or a feed, and it will notify you about new entries!

# Supported commands

```
start - show a greeting message
list - show your subscriptions
delete - choose subscriptions to delete
```

# Running the bot

First, create an `.env` file in the `services` folder and define there the env variables:

- `TELEGRAM_TOKEN` - the Telegram bot token. Use [@botfather](https://t.me/botfather) to get one
- `KAGGLE_USERNAME`, `KAGGLE_KEY` - [your kaggle API credentials](https://github.com/Kaggle/kaggle-api#api-credentials)

## Locally

1. Add these env variables to the same file:
    - `STORAGE_PATH` - the path where various files (such as images) will be stored
    - `DB_PATH` - the path where the database will be stored

2. Then run

```shell
pip install -r requirements.txt
python services/main/main.py
```

## With Docker Compose

1. Add these env variables to the same file:
    - `VOLUMES_ROOT` - the base path where various docker volumes will be stored
2. Create the `db`, `logs` and `storage` folders inside `VOLUMES_ROOT`
3. Run
   ```
   docker compose up --build
   ```
