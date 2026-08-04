# Quick start (Docker)

This is the recommended method for using WireGuard UI in production or for a quick try-out.

## Prerequisites

- Docker (and Docker Compose if you use the Compose method).
- The network capabilities needed to manipulate WireGuard interfaces: the container must run with `NET_ADMIN` and certain `sysctl` enabled (see below).

## Step 1 — Docker CLI

```bash
docker run -d \
  --name wireguard-ui \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -p 8000:8000 \
  -p 51820:51820/udp \
  -e ADMIN_USERNAME=admin \
  -e SECRET_KEY=your-secret-key \
  -v wg_config:/etc/wireguard \
  -v wireguard-ui_data:/var/lib/wireguard-ui \
  cyrius44/wireguard-ui:latest
```

Then open **http://localhost:8000**.

## Step 2 — Docker Compose (alternative)

```yaml
services:
  wireguard-ui:
    image: cyrius44/wireguard-ui:latest
    container_name: wireguard-ui
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1
    ports:
      - "8000:8000"
      - "51820:51820/udp"
    environment:
      - ADMIN_USERNAME=admin
      - SECRET_KEY=your-secret-key
    volumes:
      - wg_config:/etc/wireguard
      - wireguard-ui_data:/var/lib/wireguard-ui

volumes:
  wg_config:
  wireguard-ui_data:
```

```bash
docker compose up -d
```

## Step 3 — Retrieve the admin password

On the very first startup, the backend runs `seed_initial_data()` ([services/seed.py](../fonctions/services.md#seedpy)), which creates:

- the `admin` and `user` roles;
- an administrator account (`ADMIN_USERNAME`, `admin` by default) with a **randomly generated password**;
- the default global, OIDC and SMTP settings.

This password is shown **only once**, in the container logs:

```bash
docker logs wireguard-ui
```

Change it immediately from the **Profile** page once logged in.

## Step 4 — Check that the service is healthy

```bash
curl http://localhost:8000/api/health
```

```json
{ "status": "healthy", "app": "WireGuard UI", "version": "..." }
```

## Why these `cap_add` / `sysctl` are necessary

| Parameter                            | Role                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------- |
| `--cap-add NET_ADMIN`                | Allows creating/managing the `wg0` interface and `iptables` rules from the container. |
| `net.ipv4.ip_forward=1`              | Enables IP routing needed to relay peer traffic to the network.                       |
| `net.ipv4.conf.all.src_valid_mark=1` | Required so WireGuard can validate sources after packet marking (`fwmark`).           |

## Exposed ports

| Port        | Usage                              |
| ----------- | ---------------------------------- |
| `8000/tcp`  | Web interface + REST API           |
| `51820/udp` | WireGuard listening port for peers |

## Persistent volumes

| Volume              | Mount point             | Content                                    |
| ------------------- | ----------------------- | ------------------------------------------ |
| `wg_config`         | `/etc/wireguard`        | WireGuard configuration (`wg0.conf`, keys) |
| `wireguard-ui_data` | `/var/lib/wireguard-ui` | SQLite database, generated secret key      |

!!! tip "SECRET_KEY recommended in production"
Without an explicitly defined `SECRET_KEY`, the application generates one automatically at startup and persists it in `/var/lib/wireguard-ui/secret_key` — no blocking occurs. In production, still set a long, random value yourself to share sessions across multiple replicas or survive a loss of the data volume — see [Environment variables](variables-environnement.md) and [Production recommendations](../deploiement/production.md).

## Next step

Once the interface is accessible, the first configuration steps on the administrator side are:

1. Log in with the admin account.
2. Configure the **WireGuard server** — _Server_ page: network address (CIDR), listening port, then click **Generate Key Pair** to generate the server's key pair (private/public). This step is mandatory: as long as no key has been generated (or manually entered), the configuration cannot be saved or applied.
3. Fill in the **endpoint address** — _Global Settings_ page, **Endpoint Address** field: this is the public hostname (e.g. `vpn.example.com`) or public IP address by which WireGuard clients will reach the server. Without this value, the configuration files generated for clients will be incorrect and clients will not be able to connect — set it before creating peers.
4. Create the first **peers (clients)** — _Clients_ page.
5. Optionally configure **SMTP** (sending config by email) and **OIDC** (SSO).

!!! warning "Important order"
Always generate the **server keys** and fill in the **endpoint address** before creating clients. A peer created before these two elements are defined will produce an invalid `.conf`/QR code configuration (missing server public key or endpoint), which will need to be regenerated and resent to the client once the server is properly configured.

These screens correspond to the routers documented in [Routers (endpoints)](../fonctions/routers.md) (`server.py` for the keys, `settings.py` for the endpoint).
