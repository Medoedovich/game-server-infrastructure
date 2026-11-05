# Arma Reforger Dedicated Server

Self-hosted Arma Reforger dedicated server using Docker Compose and FRP.

The game server runs on a home Linux machine, while a public VPS provides an external IP address through FRP.

**Status:** Experimental. Based on a working deployment, but the portable configuration has not yet been fully validated.

## Requirements

- Linux server with Docker Engine and Docker Compose
- Public VPS with FRP server (`frps`)
- FRP client (`frpc`) on the home server
- Open UDP ports on the VPS
- Sufficient CPU, RAM, disk space, and network bandwidth

## Architecture

Players connect to the public VPS on UDP ports 2001 and 17777. The FRP server forwards traffic through the FRP connection to the client running on the home Linux server. The client forwards traffic to the Arma Reforger Docker container.

## Network ports

| Port | Protocol | Purpose | Public access |
|---|---|---|---|
| 2001 | UDP | Game traffic | Required |
| 17777 | UDP | Server query | Required |
| 19999 | UDP | RCON | Not exposed by default |
| 7000 | TCP | FRP transport | VPS only |

The VPS firewall must allow incoming UDP traffic on ports 2001 and 17777.

## Installation

Clone the repository on the home Linux server.

Copy `.env.example` to `.env` inside `games/arma-reforger/` and configure the public VPS address, server name, scenario, and passwords.

Start the game server with `docker compose up -d`.

Check its status using `docker compose ps` and `docker compose logs --tail=100`.

## FRP configuration

The shared FRP client is configured under `infra/frp/`.

Copy `games/arma-reforger/frpc.toml.example` to `infra/frp/confd/arma-reforger.toml`.

The shared FRP client must load proxy configurations from `confd/`.

Do not start a second FRP client if one is already running.

## VPS firewall

On a VPS using UFW, allow UDP ports 2001 and 17777.

Ensure the FRP transport port is accessible to the home server.

Avoid exposing RCON publicly unless explicitly required and secured.

## Persistent data

Game server files are stored under `data/`.

This directory is excluded from Git and must be backed up separately.

The Docker Compose configuration uses bind mounts under `data/` for game files and a named Docker volume (`steamcmd`) for SteamCMD data.

The `data/` directory is excluded from Git. Both bind-mounted data and Docker volumes require an appropriate backup strategy.

See [Arma Reforger validation](../../docs/arma-reforger-validation.md) for the current validation status and remaining tests.

## Troubleshooting

If the server appears in the server browser but players cannot connect:

1. Verify that the game container is running.
2. Verify that `frpc` is connected to `frps`.
3. Check UDP 2001 and 17777 in the VPS firewall.
4. Check the FRP proxy configuration.
5. Inspect the game server logs.

A working FRP connection does not automatically mean that the VPS firewall permits incoming game traffic.

## Security

- Use strong, unique FRP and RCON credentials.
- Never commit real credentials.
- Keep RCON inaccessible from the public Internet by default.
- Review firewall rules before deployment.
- Back up persistent server data before upgrades.
