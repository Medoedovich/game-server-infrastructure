# Battlefield 2 Dedicated Server

Docker-based Battlefield 2 v1.5 dedicated server infrastructure with BF2Statistics, PRMasterServer, MariaDB, and automatic player synchronization.

## Overview

This directory documents the Battlefield 2 server deployment tested on `ryzen-server` (Ubuntu 24.04).

The deployment provides:

- Battlefield 2 v1.5 dedicated server
- BF2Statistics 3.3.0
- MariaDB statistics database
- PRMasterServer account services
- Automatic synchronization between PRMasterServer and BF2Statistics

The deployment is currently a test environment.

## Components

| Service | Docker image | Purpose |
|---|---|---|
| `bf2` | `startersclan/docker-bf2:v1.5.3153.0-bf2stats-3.3.0` | Battlefield 2 dedicated server |
| `asp` | `startersclan/asp:3.3.0` | BF2Statistics ASP |
| `db` | `mariadb:10.8` | Statistics database |
| `prmasterserver` | `startersclan/prmasterserver:v0.1.0` | Account and GameSpy-compatible services |
| `player-sync` | Locally built Python 3.12 image | Player account synchronization |

## Architecture

The main Docker Compose project is named `bf2-test`.

It contains four services:

- `bf2`
- `asp`
- `db`
- `prmasterserver`

The `player-sync` service runs in a separate Compose project.

### Docker Networks

**bf2-network**

Connects:

- Battlefield 2
- BF2Statistics ASP
- MariaDB
- player-sync

**gamespy-network**

Connects:

- Battlefield 2
- PRMasterServer

BF2Statistics ASP provides internal DNS aliases for statistics-related GameSpy hostnames.

PRMasterServer provides internal DNS aliases for account and master-server hostnames.

### Account Synchronization

PRMasterServer stores accounts in SQLite.

BF2Statistics stores player records in MariaDB.

The separate `player-sync` service reads PRMasterServer accounts and creates missing BF2Statistics player records.

Player IDs are calculated as:

`BF2Statistics PID = 100000000 + PRMasterServer account ID`

Synchronization is one-way and does not transfer passwords.

See [Player Synchronization](player-sync/README.md) for implementation details.

## Network Ports

### Battlefield 2

| Port | Protocol | Purpose |
|---|---|---|
| 16567 | UDP | Game server |
| 29900 | UDP | Game server query |

### PRMasterServer

| Port | Protocol |
|---|---|
| 29900 | TCP |
| 29901 | TCP |
| 28910 | TCP |
| 27900 | UDP |
| 29910 | UDP |

In the tested deployment, PRMasterServer ports are bound to the host LAN address `192.168.1.73`.

This address is environment-specific and must be adjusted for other hosts.

### BF2Statistics ASP

The ASP service is published on:

`127.0.0.1:8081 -> 80/tcp`

It is not directly exposed on the host's external network interfaces.

## Persistent Storage

The main Compose deployment uses named Docker volumes for:

- MariaDB data
- PRMasterServer SQLite data
- BF2Statistics cache
- BF2Statistics configuration
- BF2Statistics logs
- BF2Statistics snapshots
- BF2Statistics backups

The player synchronization service mounts the PRMasterServer SQLite volume read-only.

## Configuration

The tested BF2 deployment uses bind-mounted configuration files:

- `config/bf2/serversettings.con`
- `config/bf2/maplist.con`
- `config/bf2/BF2StatisticsConfig.py`

MariaDB initialization also depends on SQL and configuration files from the BF2Statistics source tree.

These dependencies must be available before reproducing the main Compose deployment.

The current repository documentation does not yet provide a complete standalone deployment of all Battlefield 2 services.

## Restart Policy

The four main services currently use:

`restart: "no"`

This preserves the manually controlled test environment.

The separate `player-sync` service uses:

`restart: unless-stopped`

Do not change the restart policies without reviewing the intended deployment behavior.

## Security

- Database passwords are supplied through environment variables.
- Real `.env` files must not be committed.
- BF2Statistics ASP is bound to localhost.
- Player synchronization uses a dedicated MariaDB account with limited privileges.
- Player synchronization runs as a non-root user.
- The SQLite volume is mounted read-only in `player-sync`.
- Docker container capabilities are dropped for `player-sync`.
- The `player-sync` root filesystem is read-only.

## Repository Structure

```text
games/battlefield-2/
├── README.md
└── player-sync/
    ├── README.md
    ├── Dockerfile
    ├── compose.yaml
    ├── .dockerignore
    ├── .env.example
    ├── requirements.txt
    └── sync.py
```

## Deployment Status

The player synchronization component has been implemented and tested successfully.

Verified behavior includes:

- Reading PRMasterServer SQLite accounts
- Detecting missing BF2Statistics player records
- Creating records with matching player IDs
- Detecting conflicting records without overwriting them
- Recovering from simulated database connection failures
- Running with restricted container privileges
- Successful game connection using an automatically synchronized account

The full Battlefield 2 deployment remains under testing.

## Future Work

- Document and version the main Battlefield 2 Compose configuration.
- Prepare sanitized BF2 server configuration examples.
- Document BF2Statistics database initialization.
- Document network exposure and external connectivity.
- Define a reproducible deployment procedure.
- Review restart policies before production deployment.
