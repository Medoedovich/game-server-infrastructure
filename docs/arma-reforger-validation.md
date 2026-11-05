# Arma Reforger Module Validation

## Status

**Partially validated — not yet production-tested as a fresh deployment.**

The module is based on an existing working Arma Reforger server. Its portable Docker Compose configuration has been validated separately.

## Environment

- Host operating system: Linux
- Container runtime: Docker Engine with Docker Compose
- Image: `ghcr.io/acemod/arma-reforger:latest`
- Networking: FRP v0.69.1 through a public VPS

## Docker Compose validation

The module was checked using:

`docker compose config --quiet`

**Result:** Exit code `0`.

This confirms that Docker Compose accepts the configuration. It does not confirm successful game-server startup.

## Environment variables

The following variable names were confirmed in the running container and the inspected image:

- `SERVER_PUBLIC_ADDRESS`
- `GAME_NAME`
- `GAME_MAX_PLAYERS`
- `GAME_PASSWORD`
- `GAME_SCENARIO_ID`
- `GAME_MODS_IDS_LIST`
- `RCON_PASSWORD`

Variable presence does not independently establish correct runtime behavior for every value.

## Network ports

The running server uses:

| Port | Protocol | Purpose |
|---|---|---|
| 2001 | UDP | Game |
| 17777 | UDP | Server query |
| 19999 | UDP | RCON |

The portable Compose template publishes RCON only on `127.0.0.1`.

The existing production container publishes RCON on all host interfaces. This difference is intentional and has not yet been runtime-tested.

## Persistent storage

The inspected image declares these volumes:

- `/home/profile`
- `/reforger/Configs`
- `/reforger/workshop`
- `/steamcmd`

The portable Compose template also mounts `/reforger/addons`.

A named volume is used for `/steamcmd` to make its lifecycle easier to manage.

The named volume was validated using `docker compose config --format json`. Docker Compose reported:

- Volume name: `steamcmd`
- Mount type: `volume`
- Mount target: `/steamcmd`

## Container startup

The inspected image specifies:

`python3 /launch.py`

The portable Compose template does not override this command.

## Remaining validation

Before marking the module production-ready:

1. Test a fresh deployment in an isolated environment.
2. Confirm that the game server starts successfully.
3. Verify public connectivity through FRP.
4. Verify that game data persists across container recreation.
5. Test the intended RCON access configuration.
6. Confirm the behavior of all required environment variables.

## Safety

Validation was performed without starting a second game-server container or modifying the running production deployment.
