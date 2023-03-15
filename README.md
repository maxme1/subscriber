## Supported commands

```
start - show a greeting message
list - show your subscriptions
delete - choose subscriptions to delete
```

## Running the bot

### Preparation

1. Choose a root for your volumes and point the `VOLUMES_ROOT` env variable to it
2. Create the `db`, `logs` and `storage` folders inside the root
3. Place a `.env` file in the `services` folder and define there the env variables:
    - `TELEGRAM_TOKEN` - the Telegram bot token. Use @botfather to get one
    - `KAGGLE_USERNAME`, `KAGGLE_KEY` - [your kaggle API credentials](https://github.com/Kaggle/kaggle-api#api-credentials)

### Run

```
docker-compose up --build
```

### Troubleshooting

Error:

```
Error: GDK_BACKEND does not match available displays
```

Fix: `https://stackoverflow.com/a/51162392`
