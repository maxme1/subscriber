## Supported commands

```
list - show your subscriptions
delete - choose subscriptions to delete
```

### Migrating the DB

E.g.

```python
from playhouse.migrate import *

from subscriber.database import DATABASE

migrator = SqliteMigrator(DATABASE)

migrate(
    migrator.add_column('channel', 'image', CharField(default='')),
)

```

### Troubleshooting

Error:

```
Error: GDK_BACKEND does not match available displays
```

Fix: `https://stackoverflow.com/a/51162392`
