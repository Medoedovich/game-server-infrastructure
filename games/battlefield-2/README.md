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

The main Battlefield 2 deployment is defined in `compose.yaml`.

The repository includes the following configuration files:

- `.env.example` — environment variable template
- `config/bf2/serversettings.con` — Battlefield 2 server settings
- `config/bf2/maplist.con` — map rotation
- `config/bf2/BF2StatisticsConfig.py.example` — sanitized BF2Statistics configuration template

The runtime configuration file `config/bf2/BF2StatisticsConfig.py` is created from its example and is excluded from Git because it contains authentication credentials.

The local `.env` file is also excluded from Git.

MariaDB initialization requires SQL and configuration files from the BF2Statistics ASP source repository. These files are not duplicated in this repository.

The tested ASP source revision is:

`88b62c04c1938a5b3b7e9e74c72bfc54d6092bc6`

See the [Deployment](#deployment) section for instructions on preparing the required dependencies and configuration files.

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
├── compose.yaml
├── .env.example
├── config/
│   └── bf2/
│       ├── serversettings.con
│       ├── maplist.con
│       └── BF2StatisticsConfig.py.example
└── player-sync/
    ├── README.md
    ├── Dockerfile
    ├── compose.yaml
    ├── .dockerignore
    ├── .env.example
    ├── requirements.txt
    └── sync.py
```

The following local files and directories are excluded from Git:

- `.env` — deployment credentials and environment settings
- `config/bf2/BF2StatisticsConfig.py` — runtime statistics authentication configuration
- `sources/` — external BF2Statistics ASP source tree

The main Compose stack and the player synchronization service are maintained as separate deployments.

## Deployment

This section describes how to prepare and start the main Battlefield 2 Docker Compose stack. The separate player synchronization service is documented in [player-sync/README.md](player-sync/README.md).

The procedure is based on the tested configuration on `ryzen-server`. A complete clean-host deployment has not yet been independently verified.

### Prerequisites

- Linux host with Docker Engine and Docker Compose
- Access to the required container images
- An IP address assigned to the Docker host for PRMasterServer port bindings
- BF2Statistics ASP source files at the tested revision

### Prepare ASP Dependencies

From the `games/battlefield-2/` directory:

```sh
mkdir -p sources
git clone https://github.com/startersclan/asp.git sources/asp
git -C sources/asp checkout --detach 88b62c04c1938a5b3b7e9e74c72bfc54d6092bc6
```

The main Compose configuration requires these files:

- `sources/asp/src/ASP/system/sql/schema.sql`
- `sources/asp/src/ASP/system/sql/data.sql`
- `sources/asp/config/db/setup.sql`
- `sources/asp/config/db/my.cnf`

The `sources/` directory is excluded from Git.

### Prepare Environment Variables

Create the local environment file:

```sh
cp .env.example .env
```

Edit `.env` and configure:

- `BF2_BIND_IP` — an IP address assigned to the Docker host
- `DB_ROOT_PASSWORD` — a strong, unique MariaDB root password

Do not commit `.env` to Git.

### Prepare BF2Statistics Configuration

Create the runtime configuration:

```sh
cp config/bf2/BF2StatisticsConfig.py.example config/bf2/BF2StatisticsConfig.py
```

The example contains a placeholder authentication token.

BF2Statistics validates the `stats_auth_id` and `stats_auth_token` values against the `stats_provider` table in MariaDB.

The upstream initialization data creates a default statistics provider with `auth_id = 112950` and a predefined token.

Before starting the game server, configure a matching token in both the database and `BF2StatisticsConfig.py`. For public deployments, replace the upstream default token with a unique secret.

The upstream `setup.sql` also authorizes the default provider and configures the IPv4 authorization range as `0.0.0.0/0`. Review and restrict this setting before exposing the deployment publicly.

### Validate Docker Compose

```sh
docker compose config --quiet
```

This checks Compose configuration syntax and variable resolution. It does not verify successful application initialization.

### Database Initialization

For a new MariaDB data volume, the container processes the mounted initialization scripts in filename order:

1. `01-schema.sql` — database schema
2. `02-data.sql` — initial data
3. `03-setup.sql` — additional configuration and records

The scripts originate from the pinned ASP source revision.

Initialization scripts are not automatically reapplied when an existing database volume is reused.

**Do not delete an existing database volume to force reinitialization.** This can permanently destroy player statistics.

### Start the Main Stack

After preparing the environment, initializing the database as required, and configuring authentication:

```sh
docker compose up -d
docker compose ps
```

The main services are:

- `db` — MariaDB
- `asp` — BF2Statistics ASP
- `prmasterserver` — account and master server
- `bf2` — Battlefield 2 dedicated server

The current Compose configuration uses `restart: "no"` to preserve manual control of the test environment.

The separate `player-sync` service requires its own configuration and database permissions. Follow [player-sync/README.md](player-sync/README.md) after preparing the main stack.

### Deployment Limitations

- A complete deployment on a clean host has not yet been verified.
- The secure token rotation procedure requires additional testing.
- Public network exposure and firewall configuration require separate validation.
- Restart policies must be reviewed before production deployment.

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

- Verify the complete Battlefield 2 deployment procedure on a clean host.
- Implement and test secure BF2Statistics authentication token rotation.
- Restrict BF2Statistics provider IP authorization for production use.
- Document and validate external connectivity through the VPS and FRP infrastructure.
- Review firewall rules and publicly exposed network ports.
- Review restart policies before production deployment.
- Validate the complete stack together with the separate player synchronization service.
- Prepare a migration procedure for persistent database and account data.
