# Arma Reforger — Production Deployment Audit

> **Status:** Read-only audit based on observations from 7 November 2026. This is a point-in-time inventory, not a tested disaster-recovery procedure.
>
> **Safety:** Do not change or redeploy the live stack to match the repository example. Never commit `stack.env`, credentials, RCON passwords, private keys, or unreviewed generated server configuration to this public repository.

## Scope and sources

This audit compares the running `arma-reforger` container on `ryzen-server`, its Portainer-managed Compose definition, the local container image metadata, and the repository template at [`games/arma-reforger/compose.yaml`](../games/arma-reforger/compose.yaml). Inspection was read-only, except for manually invoking the image's health-check script; no deployment or configuration changes were made.

## Deployment ownership and file locations

| Item | Observed value |
| --- | --- |
| Host | `ryzen-server` |
| Container / Compose project | `arma-reforger` / `arma-reforger` |
| Image | `ghcr.io/acemod/arma-reforger:latest` |
| Platform | `linux/amd64` |
| Restart policy | `unless-stopped` |
| Portainer volume | `portainer_data` |
| Compose path inside Portainer | `/data/compose/4/docker-compose.yml` |
| Compose path on host | `/var/lib/docker/volumes/portainer_data/_data/compose/4/docker-compose.yml` |
| Environment file on host | `/var/lib/docker/volumes/portainer_data/_data/compose/4/stack.env` |
| Game-data directory on host | `/data/compose/4/reforger/` |

The `/data/compose/4` path in Docker Compose labels refers to the working directory used by Portainer. Portainer's `/data` is backed by the `portainer_data` Docker volume, **not** the host's `/data` directory. The production Compose definition and game-data bind mounts therefore reside in separate host locations.

The environment file was not read or copied for this audit. Its existence was confirmed by directory listing only.

## Runtime mounts

| Container destination | Mount type | Host source |
| --- | --- | --- |
| `/reforger/Configs` | Bind | `/data/compose/4/reforger/configs` |
| `/home/profile` | Bind | `/data/compose/4/reforger/profile` |
| `/reforger/workshop` | Bind | `/data/compose/4/reforger/workshop` |
| `/reforger/addons` | Bind | `/data/compose/4/reforger/addons` |
| `/steamcmd` | Anonymous Docker volume | Docker-managed volume (observed via `docker inspect`) |

The image declares volumes for `/home/profile`, `/reforger/Configs`, `/reforger/workshop`, and `/steamcmd`. Since the production Compose file does not explicitly mount `/steamcmd`, Docker has attached an anonymous volume. Its data must be accounted for in any migration or recovery plan; a fresh deployment may allocate a different volume.

## Networking and published ports

The running container is attached to the existing external Docker network `reforger-net`. The production Compose definition explicitly requires this network.

| UDP port | Production Compose | Repository template |
| --- | --- | --- |
| `2001` | `2001:2001/udp` | Same |
| `17777` | `17777:17777/udp` | Same |
| `19999` (RCON) | `19999:19999/udp` | `127.0.0.1:19999:19999/udp` |

**RCON exposure:** Production publishes UDP 19999 on all host interfaces, whereas the repository template binds it to host loopback only. This is a meaningful exposure difference, but effective internet reachability depends on host firewall rules, FRP forwarding, and other network controls. Do not change the binding before validating the intended administration path and connectivity.

## Differences from the repository template

| Area | Production | Repository template | Implication |
| --- | --- | --- | --- |
| Persistent bind paths | `./reforger/...` | `./data/...` | A direct substitution may mount empty or incorrect directories. |
| SteamCMD storage | Implicit anonymous volume | Explicit named volume `steamcmd` | Migration must preserve or intentionally replace existing data. |
| Network | External `reforger-net` | No explicit external network | Connectivity to other containers may differ. |
| Healthcheck | Explicit UDP socket check | Inherits image healthcheck | Different health semantics. |
| RCON publishing | All interfaces | Loopback | Different exposure and administration path. |
| Environment syntax | `${VARIABLE}` substitutions | Required checks and defaults for selected variables | Different validation and fallback behavior. |
| `GAME_PASSWORD` | Not present in inspected production Compose | Optional variable in template | No conclusion about actual server access policy without further inspection. |

The observed production environment entries include `SERVER_PUBLIC_ADDRESS`, `GAME_NAME`, `GAME_MAX_PLAYERS`, `RCON_PASSWORD`, `GAME_SCENARIO_ID`, and `GAME_MODS_IDS_LIST`. Values were not disclosed. The production Compose uses list-style environment entries; the template uses mapping-style entries.

## Healthcheck analysis

**Production override:**

```yaml
healthcheck:
  test: ["CMD-SHELL", "netstat -anu | grep :2001 || exit 1"]
  interval: 1m
  timeout: 10s
  retries: 3
```

This checks whether a UDP socket matching port 2001 appears in `netstat` output. It does not establish that the game server responds to clients.

**Image default:** `python3 /app/healthcheck.py`, with a 60-second interval, 30-second Docker timeout, three retries, and a 15-minute start period. The production container retains the 15-minute start period from the image, while overriding the test and timeout.

The image's Python script reads A2S settings from the selected server configuration, falling back to environment variables if that file does not exist. When A2S is configured, it sends an A2S_INFO UDP query and accepts a nonempty reply. When A2S is absent or incomplete, it exits successfully **without probing the server**. The script does not validate the returned packet's contents.

Observed generated configuration `/data/compose/4/reforger/configs/docker_generated.json` contains `a2s.address = 0.0.0.0` and `a2s.port = 17777`. A manual execution of `python3 /app/healthcheck.py` inside the running container returned exit code `0`. This is consistent with a successful A2S probe, **provided** the container selected that configuration; the `ARMA_CONFIG` override was not independently checked. No production healthcheck setting was changed.

The running container's image ID matched the locally tagged `latest` image ID at inspection time (`sha256:beb50bcaebbc3b3124363ed1c0a5729b514493d72b3cadd52a204ade6105fecd`). This does not pin the mutable `latest` tag for future deployments.

## Recovery and maintenance considerations

1. **Back up both storage locations:** Portainer stack definition and environment file in `portainer_data`, plus game-data bind directories under host `/data/compose/4/reforger/`. Keep backups encrypted and outside the public repository.
2. **Inventory the anonymous SteamCMD volume:** Record its Docker volume identity and decide how it will be restored or migrated before recreating the container. Do not prune Docker volumes indiscriminately.
3. **Preserve network dependencies:** Document creation, ownership, and consumers of `reforger-net` before attempting deployment from the repository template.
4. **Review RCON exposure:** Confirm the intended route through the VDS/FRP, firewall, and administrative tooling before proposing a production port-binding change.
5. **Choose health semantics deliberately:** The image's A2S-based check is preferable when A2S is configured and reachable, but its no-op behavior when A2S is absent must be understood. Verify `ARMA_CONFIG` before treating the manual success as conclusive.
6. **Avoid blind redeployment:** Production and repository Compose definitions are not interchangeable without explicit data-path, network, and volume migration decisions.
7. **Consider immutable image references:** A pinned version or digest would improve reproducibility; test and approve any image change separately.

## Outstanding verification

- Confirm the container's effective `ARMA_CONFIG` selection without exposing unrelated environment values.
- Confirm actual A2S response behavior and external reachability separately from the manual script's exit code.
- Document `reforger-net` creation and cross-container dependencies.
- Audit host firewall and FRP rules affecting UDP 19999 before changing RCON publication.
- Establish a tested backup-and-restore procedure covering Portainer configuration, game-data bind mounts, and the anonymous SteamCMD volume.
- Determine whether the repository template is intended as a clean-install example or an exact reproducible representation of production.

## Change policy

This document records observations and recommendations only. No live-service modification, container recreation, volume migration, network change, or Portainer stack update is authorized by this audit.
