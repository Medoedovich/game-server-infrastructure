# Home Server — `ryzen-server`

> **Status:** Observed infrastructure inventory, 7 November 2026. This document records inspection results; it is not a complete deployment or recovery procedure.
>
> **Safety:** Do not copy production secrets, private keys, authentication tokens, passwords, or unreviewed configuration files into the public repository. Do not change running services to make them match examples.

## Role and host

`ryzen-server` is the home Linux host for game servers, statistics services, reverse proxying, and the FRP client. A public VDS (`che-bu-rek`) provides external entry points. See [architecture.md](architecture.md) for the cross-host topology.

| Property | Observed value |
| --- | --- |
| Hostname | `ryzen-server` |
| Operating system | Ubuntu 24.04.4 LTS, x86_64 |
| LAN interface | `enp7s0` |
| LAN IPv4 address | `192.168.1.73/24` |
| Container runtime | Docker Engine / Docker Compose |
| Host firewall | UFW active; deny incoming, allow outgoing, deny routed by default |
| Host WireGuard interfaces | None shown by `wg show interfaces` during inspection |

The absence of a host WireGuard interface does not mean DayZ lacks VPN connectivity: DayZ uses a WireGuard container. The proposed administrative VPN interface `wg-admin` was not present on this host during inspection.

## Running containers

Nine containers were running during inspection. Their runtime state is a point-in-time observation, not a guarantee of application health or external reachability.

| Container | Compose project | Service | Network mode / network | Role |
| --- | --- | --- | --- | --- |
| `arma-reforger` | `arma-reforger` | `arma-reforger` | `reforger-net` | Arma Reforger dedicated server |
| `dayz` | `dayz` | `dayz` | Shares `dayz-wg` network namespace | DayZ dedicated server |
| `dayz-wg` | `dayz` | `wireguard` | `dayz_default` | WireGuard networking for DayZ |
| `dayz-stats-ingest-1` | `dayz-stats` | `ingest` | `dayz-stats_default` | Statistics ingestion |
| `dayz-stats-db-1` | `dayz-stats` | `db` | `dayz-stats_default` | PostgreSQL |
| `dayz-stats-grafana-1` | `dayz-stats` | `grafana` | `dayz-stats_default` | Grafana |
| `reforger-stats-caddy` | `backend` | `caddy` | `reforger-net` | Caddy HTTP/HTTPS proxy |
| `system-frpc` | `frpc` | `frpc` | `host` | FRP client |
| `portainer` | No Compose project label | No Compose service label | `bridge` | Docker management |

`portainer` has no Docker Compose project/service labels. Its creation and lifecycle mechanism have not been established.

### Observed Compose configuration paths

These are paths on the running home host, **not** repository paths:

| Compose project | Production configuration path |
| --- | --- |
| `arma-reforger` | `/data/compose/4/docker-compose.yml` |
| `dayz` | `/data/compose/15/docker-compose.yml` |
| `frpc` | `/data/compose/13/docker-compose.yml` |
| `dayz-stats` | `/home/phil/dayz-stats/docker-compose.yml` |
| `backend` | `/data/compose/reforger-stats/backend/docker-compose.yml` |

The `backend` project had a mixed Compose status (`exited(2), running(1)`); only its running Caddy container was included in the `docker ps` inventory. The identities and expected state of its exited services have not been inspected.

## Networking and published ports

### Container networks

- `reforger-net`: shared by `arma-reforger` and `reforger-stats-caddy`.
- `dayz_default`: contains the `dayz-wg` network endpoint; `dayz` shares its network namespace.
- `dayz-stats_default`: contains ingestion, PostgreSQL, and Grafana containers.
- Host network: `system-frpc` uses the host network stack.
- Default Docker `bridge`: used by `portainer`.

### Observed Docker host bindings

| Container | Published host ports |
| --- | --- |
| `arma-reforger` | UDP `2001`, `17777`, `19999` on all IPv4/IPv6 host interfaces |
| `dayz-wg` | UDP `2302`, `8766`, `27016` on all IPv4/IPv6 host interfaces; UDP `51821` on `127.0.0.1` |
| `dayz-stats-grafana-1` | TCP `3000` on all IPv4/IPv6 host interfaces |
| `reforger-stats-caddy` | TCP `80`, `443` on all IPv4/IPv6 host interfaces; UDP `443` also shown |
| `portainer` | TCP `9000` on all IPv4/IPv6 host interfaces |

These bindings do **not** prove that the ports are reachable from the public internet. Docker NAT/filter rules, UFW, LAN routing, and FRP must be considered together. In particular, the active Arma Reforger deployment binds RCON UDP `19999` to all host interfaces, whereas the repository's [portable Compose example](../games/arma-reforger/compose.yaml) binds it to `127.0.0.1`.

### FRP client

The `system-frpc` container uses `fatedier/frpc:v0.69.1` and host networking. The observed production Compose project is `frpc` at `/data/compose/13/docker-compose.yml`.

The repository contains [FRP templates](../infra/frp/) and [validation notes](frp-validation.md), but those templates have not been verified as identical to the active production configuration. Do not start another FRP client with duplicate production proxy definitions. Do not publish live FRP tokens or unredacted configuration.

## DayZ networking

The `dayz` container uses `network_mode: container:<dayz-wg-container-id>` in the inspected Docker runtime. This means its network stack is provided by the `dayz-wg` container rather than a separate DayZ network endpoint.

The VDS has an active DayZ WireGuard interface `wg0` (`10.8.0.1/24`) with a recent handshake for peer `10.8.0.2/32` at inspection time. The home-side WireGuard implementation runs inside Docker, so it is not expected to appear in host-level `wg show interfaces` output.

Do not change the working DayZ tunnel as part of administrative VPN work.

## DayZ automatic update

| Item | Observed state |
| --- | --- |
| Timer | `dayz-update.timer` exists and has a scheduled next run |
| Service | `dayz-update.service`: `static`, `inactive` when inspected |
| Script | `/usr/local/sbin/dayz-update.sh`, executable |
| Scheduled next run at inspection | 9 November 2026, 09:00 UTC |

An inactive timer-triggered service can be normal between executions. The timer's enabled state, script internals, notification behavior, and recovery behavior have not been audited in this inventory. Do not infer update success from the presence of the timer alone.

## Host firewall

UFW was active with logging set to `low`. Defaults were `deny (incoming)`, `allow (outgoing)`, and `deny (routed)`.

Observed inbound allowances (IPv4 and IPv6):

| Port / protocol | Rule |
| --- | --- |
| `22/tcp` | Allow incoming (SSH) |
| `9090/tcp` | Allow incoming (service identity not independently verified) |
| `137,138/udp` | Allow incoming (Samba) |
| `139,445/tcp` | Allow incoming (Samba) |

UFW output did not show explicit inbound allow rules for Docker-published game, Portainer, Grafana, or Caddy ports. This is **not** evidence that Docker-published ports are inaccessible: Docker-managed firewall/NAT rules can affect the effective exposure. No external reachability tests were performed.

## Repository coverage and known gaps

- [Arma Reforger module](../games/arma-reforger/README.md) and [validation notes](arma-reforger-validation.md) describe a portable example, not a fully validated reproduction of production.
- [FRP validation](frp-validation.md) covers syntax/includes behavior, not a complete production traffic audit.
- DayZ, statistics, Caddy, Portainer, and update automation are not yet fully represented by reviewed portable modules in this repository.
- Production Compose files have not been compared line by line with repository examples.
- The VDS administrative WireGuard interface exists, but the home host did not have `wg-admin` during inspection. End-to-end administrative VPN access is unverified.

## Follow-up checks (read-only first)

1. Determine how Portainer is started and managed.
2. Identify the two exited services in the `backend` Compose project and whether their state is expected.
3. Review production Compose settings with secrets redacted before comparing them to repository templates.
4. Establish effective LAN/public exposure of Docker-published ports, particularly Portainer, Grafana, and RCON.
5. Verify `dayz-update.timer` activation, script behavior, notifications, and failure recovery separately.
6. Document persistent data locations, backups, and restoration tests before attempting deployment changes.
7. Validate the administrative VPN path before replacing existing FRP-based administrative access.

## Operational boundaries

- No production changes were made as part of this inventory.
- Do not commit production `.env` files, WireGuard private keys, FRP tokens, or passwords.
- Treat runtime paths and container identifiers as observations that can change after redeployment.
- Validate and back up a service before changing its Compose project, network mode, or published ports.
