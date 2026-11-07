# Public VDS — `che-bu-rek`

> **Status:** Observed infrastructure inventory, based on inspections in November 2026. This is not a complete, independently validated deployment specification.
>
> **Security:** Do not publish production FRP authentication tokens, WireGuard private or preshared keys, credentials, or unredacted configuration files.

## Role in the infrastructure

`che-bu-rek` is the public-facing VDS for game-server infrastructure hosted primarily on `ryzen-server`. It provides FRP ingress and WireGuard endpoints. Configuration development and Git operations take place on the administrator's MacBook Air.

For the broader topology, see [Architecture](architecture.md). For the home host, see [ryzen-server](ryzen-server.md).

## Host inventory

| Attribute | Observed value |
| --- | --- |
| Hostname / DNS name | `che-bu-rek.ru` |
| Operating system | Ubuntu 18.04.6 LTS, x86_64 |
| Public IPv4 | `45.133.247.107/24` on `ens3` |
| Public IPv6 | `2a0a:9302:1:150::1/48` on `ens3` |
| Docker | Not installed at inspection time |
| Firewall | UFW active |
| FRP server | Native executable managed by systemd |
| WireGuard | `wg0` and `wg-admin` interfaces observed |

Ubuntu 18.04 is outside its standard support period. Any operating-system migration requires its own backup, access-preservation, and rollback plan; this document does not authorize an upgrade.

## FRP server (`frps`)

The active FRP server is **not** deployed using the repository's Docker Compose example.

| Component | Observed path / service |
| --- | --- |
| Executable | `/opt/frp/frps` |
| Runtime configuration | `/opt/frp/frps.toml` |
| systemd unit | `/etc/systemd/system/frps.service` |
| Service name | `frps.service` |
| State during inspection | Active (running) |
| FRP transport listener | TCP `7000` |

The actual production configuration was not published or audited line by line. In particular, the repository's `infra/frp/server/compose.yaml` and `infra/frp/frps.toml.example` must not be treated as exact copies of the running deployment.

### Observed FRP listeners

The following sockets were attributed to the `frps` process during inspection. A listener does **not** establish that a port is reachable from the internet.

| Protocol | Port(s) | Interpretation / validation status |
| --- | --- | --- |
| TCP | `7000` | FRP transport |
| UDP | `2001`, `17777` | Arma Reforger game/query traffic |
| UDP | `19999` | Arma Reforger RCON-associated proxy; external reachability not verified |
| TCP | `9000` | Portainer-associated proxy; external reachability not verified |
| UDP | `2302`, `8766`, `27016` | DayZ-associated traffic |
| UDP | `51821` | Purpose requires confirmation |
| TCP and UDP | `28001` | Purpose requires confirmation |
| TCP | `28100` | Purpose requires confirmation |
| TCP | `80`, `443` | HTTP/HTTPS listeners; upstream destinations not confirmed |

The precise FRP proxy names, destination addresses, authorization settings, and routing behavior remain unverified in this inventory.

## WireGuard

Two separate WireGuard networks were observed. They must not be conflated or modified as part of documentation work.

| Property | DayZ VPN | Administrative VPN |
| --- | --- | --- |
| VDS interface | `wg0` | `wg-admin` |
| VDS address | `10.8.0.1/24` | `10.9.0.1/24` |
| Listening UDP port | `51820` | `51822` |
| systemd unit | `wg-quick@wg0` | `wg-quick@wg-admin` |
| Unit state at inspection | Enabled, active | Disabled, inactive |
| Interface present | Yes | Yes |

### DayZ tunnel

- The VDS `wg0` peer was associated with `10.8.0.2`.
- A recent WireGuard handshake was observed at inspection time.
- On `ryzen-server`, DayZ uses the network namespace of the `dayz-wg` Docker container.
- The existing DayZ tunnel is operational according to the observed handshake, but end-to-end game connectivity was not re-tested for this document.

### Administrative tunnel

- The VDS `wg-admin` interface existed with address `10.9.0.1/24`.
- Peer entries were observed for `10.9.0.2/32` (home host) and `10.9.0.3/32` (administrator Mac).
- The home-host peer's last handshake was over a day old; the Mac peer had no displayed handshake at inspection time.
- No `wg-admin` interface was present on the home host when checked.
- The mechanism responsible for creating the VDS interface while its `wg-quick` unit was inactive has **not** been identified.

**Do not describe the administrative VPN as end-to-end operational.** Do not restart or enable its service solely to reconcile the apparent unit/interface mismatch. See the [administrative VPN plan](../infra/wireguard/admin/README.md), whose deployment status requires later reconciliation with observed state.

## Firewall (UFW)

UFW was active with the following default policy:

| Direction | Default policy |
| --- | --- |
| Incoming | Deny |
| Outgoing | Allow |
| Routed | Deny |

### Observed incoming allow rules

| Protocol | Port | Likely role |
| --- | --- | --- |
| TCP | `7000` | FRP transport |
| TCP | `2222` | Purpose to confirm; do not assume it is SSH |
| UDP | `2302`, `27016`, `8766` | DayZ-related |
| UDP | `51820` | DayZ WireGuard |
| UDP | `2001`, `17777` | Arma Reforger |
| UDP | `51822` | Administrative WireGuard |

Corresponding IPv4 and IPv6 UFW entries were observed. No explicit incoming allow rule for TCP `9000` or UDP `19999` was found in the inspected allow-list, despite `frps` listening on those ports. This is **not** conclusive proof of internet inaccessibility: effective exposure also depends on other firewall layers, routes, and packet handling.

### Observed forwarding rules

- Forwarding rules were present for traffic from the DayZ `wg0` interface toward `ens3`.
- Rules were also observed for traffic from administrative peer `10.9.0.3` to home peer `10.9.0.2`, specifically TCP `9000` and UDP `19999`.
- The existence of forwarding rules does not establish that the administrative peers can communicate.

Do not modify firewall rules, forwarding policy, or access paths without an approved, tested rollback procedure.

## Repository versus running deployment

1. Production `frps` runs directly under systemd, while the repository also contains a Docker Compose server example.
2. Production FRP proxy definitions have not been compared with the repository examples.
3. The administrative WireGuard interface is present on the VDS even though its `wg-quick` unit is disabled and inactive.
4. The administrative VPN is not validated end to end; its repository README currently labels it as planned/not deployed.
5. Several observed FRP listeners (`51821`, `28001`, `28100`, and HTTP/HTTPS routing) require attribution.
6. Port exposure must be evaluated using both process listeners and effective firewall/network behavior.

## Follow-up checks (read-only first)

- Determine how `wg-admin` was created and whether any other service or script manages it.
- Review FRP proxy names and destination ports without printing credentials or authentication tokens.
- Confirm the purposes of TCP `2222`, UDP `51821`, TCP/UDP `28001`, and TCP `28100`.
- Verify public ingress and internal forwarding paths from a controlled external test host.
- Review systemd unit dependencies, restart policies, and log retention without changing them.
- Inventory backup coverage and document recovery procedures for the VDS.
- Plan an operating-system upgrade separately, preserving SSH and game connectivity.
- Reconcile the administrative VPN README after its actual state has been established.

## Change-management rules

1. Treat this document as an observation record, not a deployment runbook.
2. Keep private keys, tokens, passwords, and live unredacted configuration outside Git.
3. Do not restart `frps`, WireGuard, or UFW to validate documentation.
4. Preserve existing DayZ and Arma Reforger connectivity during future changes.
5. Test alternative administrative access before retiring any existing access path.
6. Review and commit documentation changes from the MacBook Air.
