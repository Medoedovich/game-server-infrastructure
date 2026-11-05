# FRP Server Validation

## Status

**Configuration validated — fresh deployment not yet tested.**

The FRP server module uses Docker Compose and the official FRP Docker image.

## Environment

- Container runtime: Docker Engine with Docker Compose
- Image: `fatedier/frps:v0.69.1`
- Network mode: `host`
- Configuration file: `/etc/frp/frps.toml`

## Docker Compose validation

The configuration was checked using:

```bash
docker compose config --quiet
```

**Result:** Exit code `0`.

The resolved configuration confirmed:

- Image: `fatedier/frps:v0.69.1`
- Network mode: `host`
- Command: `-c /etc/frp/frps.toml`
- Configuration mounted as a read-only bind mount

## Docker image validation

The image was successfully downloaded and inspected.

The image metadata reported:

```text
Entrypoint=["/usr/bin/frps"] Cmd=null
```

The executable was verified using:

```bash
docker run --rm \
  --network none \
  --entrypoint /usr/bin/frps \
  fatedier/frps:v0.69.1 \
  --help
```

The executable supports the `verify` command and the `-c` configuration argument.

## Configuration validation

A temporary configuration containing a listener and token authentication was tested using:

```bash
docker run --rm \
  --network none \
  -v "$HOME/frps-validation/frps.toml:/etc/frp/frps.toml:ro" \
  fatedier/frps:v0.69.1 \
  verify -c /etc/frp/frps.toml
```

**Result:**

```text
frps: the configuration file /etc/frp/frps.toml syntax is ok
```

The test used a placeholder authentication token. No production credentials were required.

## Port access policy validation

**Status: Passed — isolated functional test.**

The `allowPorts` policy was tested using FRP `v0.69.1` in an isolated Docker bridge network.

### Test configuration

The test FRP server allowed only UDP port `2001`. The client attempted to register two UDP proxies:

| Proxy | Remote port | Expected | Actual |
|---|---|---|---|
| `allowed-game-port` | 2001 | Allowed | Registered successfully |
| `denied-rcon-port` | 19999 | Denied | Rejected |

Both configuration files passed their respective `verify` checks before the functional test.

### Results

The FRP client successfully authenticated with the test server.

The allowed proxy reported:

```text
[allowed-game-port] start proxy success
```

The prohibited proxy reported:

```text
[denied-rcon-port] start error: acquire port 19999 error: port not allowed
```

The FRP server independently confirmed successful registration of the allowed proxy and rejection of the prohibited proxy.

Neither test container published Docker ports on the host. Both containers and the dedicated test network were removed after validation.

### Limitations

This test confirms that FRP enforces `allowPorts` when registering UDP proxies.

It does not establish:

- Successful end-to-end transmission of game traffic.
- Enforcement of the complete production port list.
- Firewall behavior on the public VPS.
- VPN-only access to administrative services.
- Successful deployment of the updated policy on the production VPS.

The production FRP configuration was not modified.

## Remaining validation

Before marking the FRP server module production-ready:

1. Test a fresh deployment on a separate VPS.
2. Verify end-to-end UDP and TCP forwarding.
3. Validate firewall rules on the public VPS.
4. Test the complete approved port list.
5. Implement and verify VPN-only access to Portainer and Arma Reforger RCON.
6. Verify behavior after container recreation and host reboot.
7. Document a safe migration procedure for existing deployments.

**Important:** Applying the example `allowPorts` policy to an existing FRP server may prevent previously configured proxies from registering. Review all active proxies before deployment.

## Safety

All checks were performed without starting an FRP server listener or modifying the existing production infrastructure.
