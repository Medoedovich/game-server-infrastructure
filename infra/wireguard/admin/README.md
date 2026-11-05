# Administrative WireGuard VPN

This module provides a dedicated WireGuard VPN for secure administration of game server infrastructure.

It is separate from the existing WireGuard tunnel used by DayZ.

**Status: Planned — not deployed.**

## Purpose

The administrative VPN is intended to provide private access to:

- Portainer — TCP `9000`.
- Arma Reforger RCON — UDP `19999`.
- Additional administrative services explicitly approved in the future.

Administrative services must not be exposed through public FRP proxies after migration.

## Network architecture

The VPN uses a hub-and-spoke topology with the public VPS as the central node.

| Node | Role | VPN address |
|---|---|---|
| Public VPS | WireGuard server | `10.9.0.1/24` |
| Home Linux server | WireGuard peer | `10.9.0.2/24` |
| Administrator Mac | WireGuard peer | `10.9.0.3/32` |

Configuration parameters:

- VPN network: `10.9.0.0/24`
- VPS listening port: UDP `51822`
- Linux interface: `wg-admin`
- Routing mode: Split tunnel

The VPN must not change the default routes of the home server or administrator devices.

Traffic between the administrator and home server is routed through the VPS. This requires explicit IP forwarding and firewall rules.

## Existing infrastructure

The current DayZ deployment uses a separate WireGuard tunnel:

- VPS interface: `wg0`
- VPN network: `10.8.0.0/24`
- Home endpoint: Docker container `dayz-wg`
- DayZ shares the network namespace of `dayz-wg`.

The existing DayZ tunnel must remain unchanged during administrative VPN deployment.

The FRP server currently runs as a systemd service on the VPS. The administrative VPN does not require Docker on the VPS.

## Security requirements

1. Never commit private keys, preshared keys, or production configuration files containing secrets.
2. Restrict WireGuard configuration files containing private keys to owner-only permissions (`600`).
3. Use a separate WireGuard key pair for each peer.
4. Restrict VPN access to explicitly authorized administrative services.
5. Do not route general internet traffic through the administrative VPN.
6. Do not expose Portainer or RCON publicly.
7. Preserve existing SSH access throughout deployment.
8. Validate firewall and routing rules before enabling automatic startup.

VPN membership alone does not grant unrestricted access to the home server or its Docker networks.

## Deployment plan

1. Prepare and review example WireGuard configurations.
2. Generate keys locally on the respective devices.
3. Validate the VPS and home server configurations.
4. Configure and test the VPN between the VPS and home server.
5. Connect the administrator Mac.
6. Verify connectivity between VPN peers.
7. Verify access to Portainer and Arma Reforger RCON through the VPN.
8. Implement and validate restrictive firewall rules.
9. Remove the public FRP proxies for Portainer and RCON.
10. Apply the approved FRP `allowPorts` policy after checking all active proxies.
11. Test connectivity, service restarts, and recovery procedures.
12. Document the final production configuration.

## Migration precautions

The current FRP deployment includes proxies for Portainer and Arma Reforger RCON.

Do not remove these proxies until the replacement administrative VPN has been tested.

The example FRP `allowPorts` policy excludes TCP `9000` and UDP `19999`. Applying it prematurely would prevent those existing proxies from registering.

Do not modify the existing DayZ WireGuard tunnel during migration.

## Validation status

- [x] Inspected existing WireGuard configuration on the VPS.
- [x] Inspected DayZ WireGuard networking on the home server.
- [x] Checked proposed VPN subnet against current IPv4 routes.
- [x] Checked UDP `51822` availability on the VPS and home server.
- [ ] Reviewed administrative service bindings and firewall requirements.
- [ ] Created WireGuard configuration examples.
- [ ] Generated production keys.
- [ ] Established the administrative VPN.
- [ ] Verified peer connectivity and administrative access.
- [ ] Removed public administrative FRP proxies.
- [ ] Completed production validation.
