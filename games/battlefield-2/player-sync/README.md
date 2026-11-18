# Battlefield 2 Player Synchronization

A lightweight synchronization service connecting PRMasterServer accounts with the BF2Statistics player database.

## Purpose

PRMasterServer stores registered game accounts in SQLite, while BF2Statistics maintains player records in MariaDB.

These databases are independent. A player registered through PRMasterServer may not have a corresponding BF2Statistics record.

This service automatically creates missing player records.

**It does not synchronize passwords or authentication credentials.**

## Architecture

```text
PRMasterServer (SQLite)
        |
        | Read-only access
        v
    player-sync
        |
        | SELECT / INSERT
        v
BF2Statistics (MariaDB)
```

## Synchronization Logic

1. Read account IDs and names from PRMasterServer.
2. Calculate the BF2Statistics player ID:

   `player_id = 100000000 + account_id`

3. Search the BF2Statistics `player` table by ID or name.
4. If the exact ID/name pair exists, leave it unchanged.
5. If a conflicting record exists, log the conflict and skip it.
6. If the player is missing:
   - In dry-run mode, log the proposed insertion.
   - Otherwise, insert the missing record.

New records use:

- `password`: empty string
- `country`: `xx`
- `rank_id`: `0`

Existing player records are never updated or deleted.

## Requirements

- Docker Engine with Docker Compose
- PRMasterServer SQLite database
- BF2Statistics MariaDB database
- Existing Docker network connecting the service to MariaDB
- MariaDB user with `SELECT` and `INSERT` privileges on the `player` table

The provided Compose configuration expects these existing resources:

- Docker volume: `bf2-test_master-data`
- Docker network: `bf2-test_bf2-network`

Adjust these names if your deployment uses different resources.

## Configuration

Copy the example environment file:

```sh
cp .env.example .env
chmod 600 .env
```

Configure the MariaDB credentials and connection settings.

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | MariaDB hostname | `db` |
| `DB_PORT` | MariaDB port | `3306` |
| `DB_NAME` | Database name | `bf2stats` |
| `DB_USER` | MariaDB username | Required |
| `DB_PASSWORD` | MariaDB password | Required |
| `SQLITE_PATH` | PRMasterServer SQLite database path | `/data/LoginDatabase.db3` |
| `SYNC_INTERVAL` | Polling interval in seconds | `1` |
| `DRY_RUN` | Disable insertions when `true` | `true` |

Never commit `.env` or real database credentials.

## Deployment

The example assumes the external Docker volume and network already exist.

Build and start the service:

```sh
docker compose up -d --build
```

Initially keep:

```dotenv
DRY_RUN=true
```

Inspect the logs:

```sh
docker compose logs --tail=100 player-sync
```

After validating the results, change the environment setting to:

```dotenv
DRY_RUN=false
```

Recreate the service to apply the change:

```sh
docker compose up -d --no-deps --force-recreate player-sync
```

## Security

The service runs with the following restrictions:

- Non-root user (`65534:65534`)
- Read-only container root filesystem
- Read-only SQLite volume
- All Linux capabilities dropped
- Privilege escalation disabled
- Docker log rotation enabled

The MariaDB account should have only `SELECT` and `INSERT` privileges on the BF2Statistics `player` table.

The service does not require `UPDATE` or `DELETE` privileges.

## Error Handling

Database errors are logged without terminating the synchronization loop.

Repeated errors are rate-limited to one log entry per 60 seconds.

After a failed synchronization recovers, the service logs:

```text
Synchronization recovered
```

Conflicting player records are logged but not automatically resolved.

## Limitations

- Synchronization is one-way: PRMasterServer to BF2Statistics.
- Existing records are not modified.
- Deleted or renamed PRMasterServer accounts are not propagated.
- Passwords and authentication credentials are not synchronized.
- SQLite WAL files must remain readable by the container user.
- The service expects the PRMasterServer and BF2Statistics database schemas used by the tested deployment.
