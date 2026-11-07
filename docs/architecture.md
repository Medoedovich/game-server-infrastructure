# Game Server Infrastructure — Architecture

> **Status:** Infrastructure inventory, based on observations from 7 November 2026. This document describes the observed deployment, not a fully validated or reproducible configuration.
>
> **Safety:** Never commit credentials, FRP authentication tokens, WireGuard private keys, production `.env` files, or unreviewed production configuration.

## Overview

The project separates configuration development from runtime infrastructure:

- **MacBook Air:** development workstation for Git, configuration changes, and reviews.
- **GitHub:** source repository [`Medoedovich/game-server-infrastructure`](https://github.com/Medoedovich/game-server-infrastructure). Production deployments are not yet confirmed to be driven directly from this repository.
- **`ryzen-server`:** home Linux host running Docker workloads, including game servers and related services.
- **`che-bu-rek`:** public VDS acting as an external entry point for FRP and WireGuard traffic.

```text
                      Players / administrators
                                |
                         Public internet
                                |
                 +-----------------------------+
                 | che-bu-rek (public VDS)     |
                 | Ubuntu 18.04.6 LTS          |
                 | frps (systemd)              |
                 | WireGuard wg0 / wg-admin    |
                 | UFW                         |
                 +-----------------------------+
                         |             |
                   FRP transport   DayZ WireGuard
                         |             |
                 +-----------------------------+
                 | ryzen-server (home host)    |
                 | Ubuntu 24.04.4 LTS          |
                 | Docker / Docker Compose     |
                 | frpc (host network)         |
                 | Arma Reforger / DayZ        |
                 | Statistics / Caddy          |
                 | Portainer / UFW             |
                 +-----------------------------+

    MacBook Air ---- Git ----> GitHub repository
    Mac administrative VPN peer: planned/configured on VDS,
    but end-to-end connectivity has not been validated.
```

The diagram is conceptual: it does not claim that every public port or end-to-end path has been tested.

## Home host: `ryzen-server`

| Attribute | Observed value |
| --- | --- |
| Operating system | Ubuntu 24.04.4 LTS, x86_64 |
| LAN address | `192.168.1.73/24` |
| Container runtime | Docker |
| Firewall | UFW active; default deny incoming and routed traffic |
| Administrative WireGuard interface on host | Not present at time of inspection |

### Running containers and networking

| Container | Role | Network mode / network |
| --- | --- | --- |
| `arma-reforger` | Arma Reforger dedicated server | `reforger-net` |
| `dayz` | DayZ dedicated server | Shares `dayz-wg` network namespace |
| `dayz-wg` | DayZ WireGuard container | `dayz_default` |
| `system-frpc` | FRP client | Host network |
| `reforger-stats-caddy` | HTTP/HTTPS reverse proxy | `reforger-net` |
| `dayz-stats-ingest-1` | Statistics ingestion | `dayz-stats_default` |
| `dayz-stats-db-1` | PostgreSQL | `dayz-stats_default` |
| `dayz-stats-grafana-1` | Grafana | `dayz-stats_default` |
| `portainer` | Docker administration | Default `bridge`; not associated with a Compose project in container labels |

All nine containers were running at inspection time. A container running does not by itself establish application-level reachability.

### Observed Compose project locations

| Project | Configuration path |
| --- | --- |
| `arma-reforger` | `/data/compose/4/docker-compose.yml` |
| `dayz` | `/data/compose/15/docker-compose.yml` |
| `frpc` | `/data/compose/13/docker-compose.yml` |
| `dayz-stats` | `/home/phil/dayz-stats/docker-compose.yml` |
| `backend` | `/data/compose/reforger-stats/backend/docker-compose.yml` |

These are production-side paths, not paths inside the Git repository. The repository's example Compose files must not be assumed identical to the active deployment.

### Published container ports observed

- Arma Reforger: UDP `2001`, `17777`, `19999` bound on all host interfaces; the repository example binds `19999/udp` to loopback instead.
- DayZ WireGuard container: UDP `2302`, `8766`, `27016` bound on all host interfaces; UDP `51821` bound to loopback.
- Grafana: TCP `3000` bound on all host interfaces.
- Caddy: TCP `80` and `443` bound on all host interfaces.
- Portainer: TCP `9000` bound on all host interfaces.

Docker port publication does **not** establish public internet accessibility. Docker forwarding/NAT, UFW, upstream routing, and FRP must be evaluated together.

### DayZ automatic updates

A `dayz-update.timer` is present, and its corresponding `dayz-update.service` is a static, currently inactive service. This can be normal for a timer-triggered one-shot service. The executable script exists at `/usr/local/sbin/dayz-update.sh`. Its contents and behavior have not been audited for this document.

## Public VDS: `che-bu-rek`

| Attribute | Observed value |
| --- | --- |
| Hostname | `che-bu-rek.ru` |
| Operating system | Ubuntu 18.04.6 LTS, x86_64 |
| Docker | Not installed |
| FRP server | `/opt/frp/frps`, managed by `frps.service` |
| FRP configuration | `/opt/frp/frps.toml` (contents not inspected) |
| Firewall | UFW active; default deny incoming and routed traffic |

Ubuntu 18.04 is outside standard support and warrants a separately planned operating-system migration; no upgrade is implied by this document.

### FRP listener inventory

At inspection time, `frps` was listening on:

| Protocol | Ports | Notes |
| --- | --- | --- |
| TCP | `7000` | FRP transport |
| UDP | `2001`, `17777` | Arma Reforger game/query |
| UDP | `19999` | Associated with Arma Reforger RCON; listener exists, public reachability not verified |
| TCP | `9000` | Associated with Portainer; listener exists, public reachability not verified |
| UDP | `2302`, `8766`, `27016` | DayZ-related listeners |
| UDP | `51821` | Purpose requires confirmation against live configuration |
| TCP and UDP | `28001` | Purpose not yet confirmed |
| TCP | `28100` | Purpose not yet confirmed |
| TCP | `80`, `443` | HTTP/HTTPS listeners; routing not yet confirmed |

A listening socket is not proof of access from the public internet. In particular, the observed VDS UFW allow-list did not explicitly permit incoming TCP `9000` or UDP `19999`.

### WireGuard networks

| Network | VDS interface | VDS address | Observed status |
| --- | --- | --- | --- |
| DayZ VPN | `wg0` | `10.8.0.1/24` | `wg-quick@wg0` enabled and active; recent peer handshake observed |
| Administrative VPN | `wg-admin` | `10.9.0.1/24` | Interface exists, but `wg-quick@wg-admin` disabled and inactive |

The administrative VPN has peer entries for `10.9.0.2/32` (home host) and `10.9.0.3/32` (Mac). At inspection time, the home-host peer's most recent handshake was over a day old, and no handshake was displayed for the Mac peer. No `wg-admin` interface was observed on the home host. Thus the administrative VPN must **not** be described as operational end-to-end.

VDS UFW includes forwarding allowances for Mac (`10.9.0.3`) to home host (`10.9.0.2`) for Portainer TCP `9000` and Arma Reforger RCON UDP `19999`. These are configured rules, not evidence of successful connectivity.

## Repository versus deployment

The repository includes:

- Arma Reforger Compose and configuration examples.
- FRP client and server Compose examples, plus FRP validation notes.
- Administrative WireGuard templates and a deployment plan.
- Placeholder directories for firewall rules and scripts.

Known differences and incomplete coverage:

1. The VDS actually runs `frps` as a systemd service, whereas the repository also includes a Docker Compose example.
2. The active Arma Reforger container publishes RCON UDP `19999` on all host interfaces; the repository example restricts its binding to loopback.
3. Production Compose files are outside the local Git checkout and have not been compared line by line with repository templates.
4. DayZ, statistics, Caddy, Portainer, and the update timer are not yet fully represented by portable, reviewed modules in the repository.
5. The administrative VPN templates do not represent a verified end-to-end deployment.

## Follow-up validation (read-only first)

- Identify the live FRP proxy definitions and the purpose of unclassified ports **without disclosing FRP tokens or credentials**.
- Verify which listeners are reachable externally, including the interaction between Docker port publication, FRP, UFW, and upstream networking.
- Establish how `wg-admin` was created on the VDS despite its `wg-quick` service being inactive.
- Verify the intended administrative VPN route and service access before any FRP or firewall migration.
- Compare production Compose configurations with repository templates after redacting secrets.
- Document backups and recovery procedures before changing the deployed infrastructure.
- Plan VDS OS migration separately, with rollback and connectivity safeguards.

## Change-management rules

1. Make repository changes on the MacBook Air and review them before committing or pushing.
2. Keep secrets and machine-specific production configuration out of Git.
3. Do not change working FRP, WireGuard, UFW, Docker, or game services solely to match documentation.
4. Record verified facts separately from assumptions, examples, and proposed changes.
5. Validate a replacement access path before removing any existing administrative route.
