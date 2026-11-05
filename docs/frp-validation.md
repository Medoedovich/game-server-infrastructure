# FRP Configuration Validation

This project uses FRP v0.69.1 with a shared client and modular proxy configurations.

## Configuration layout

- `infra/frp/frpc.toml.example` — shared client configuration
- `infra/frp/confd/` — enabled proxy configurations
- `games/arma-reforger/frpc.toml.example` — Arma Reforger proxy template

The shared FRP client loads additional proxy configurations using the `includes` setting.

## Validation

Run this command on a Linux host with Docker installed, from the repository root:

```bash
docker run --rm \
  --entrypoint /usr/bin/frpc \
  -v "$PWD/infra/frp/frpc.toml:/etc/frp/frpc.toml:ro" \
  -v "$PWD/infra/frp/confd:/etc/frp/confd:ro" \
  fatedier/frpc:v0.69.1 \
  verify -c /etc/frp/frpc.toml
```

Create `infra/frp/frpc.toml` from `frpc.toml.example` before validation.

The command validates the configuration without starting the FRP client or connecting to the VPS.

## Verified behavior

Tested with FRP v0.69.1:

- The main TOML configuration passed validation.
- An intentionally invalid TOML file inside `confd/` caused validation to fail.
- This confirmed that the `includes` mechanism loads additional configuration files.

These tests do not verify live network connectivity or game traffic forwarding.

## Safety

- Never commit actual FRP authentication tokens.
- Do not replace production configurations without testing.
- Do not start a second FRP client using the same proxy definitions against the production VPS.
- Validate changes before restarting production services.
