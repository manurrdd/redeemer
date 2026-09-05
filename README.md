# Redeemer

Self-hosted redemption codes for mobile apps. Your app sends `app + code + device`, Redeemer
answers whether to grant, and a small panel manages the codes and shows who redeemed them.

No user accounts, no SDK, no subscription platform. One container, one SQLite file.

```
POST /v1/redeem  {"app": "my-app", "code": "FREE99", "device_id": "…"}
              →  {"granted": true, "reason": "ok"}
```

## Why

Subscription platforms can grant access from a dashboard, but only to a user they already know:
you open a customer profile and flip a switch. There is no "generate 50 codes and let people
type them in". [Adapty's own docs](https://adapty.io/docs/grant-access-level) name the case —
a user enters a promo code in your app — and leave the code half to your backend. Licensing
servers solve a bigger problem (machine activation, entitlements, hardware locks) and coupon
systems assume a shopping cart.

This is the small piece in between, for apps that sell a one-time unlock and just want to give
some away.

## Features

- Apps, codes and redemptions in one panel; light and dark.
- Codes with a note, a usage limit, an expiry date, an on/off switch and an optional
  platform restriction (iOS, Android or both).
- Generate codes in batches, or set your own. A new batch is marked in the table and can be
  exported to CSV on its own.
- Global codes valid in every registered app.
- Redemption log with platform, app version, country and device, broken down by app, by code
  and across the global codes.
- Two modes: identified by a device UUID, or fully anonymous.
- Redeeming twice never spends a second use.
- Daily compressed backups, taken by the server itself.

## Run it

```
cp .env.example .env      # set REDEEMER_ADMIN_PASSWORD
docker compose up -d
```

The panel is at `http://localhost:8787`. Put it behind a reverse proxy with TLS before pointing a
published app at it.

### Dokploy

Create a **Compose** service from the repository, set **Compose Path** to
`./docker-compose.dokploy.yml`, add `REDEEMER_ADMIN_PASSWORD` under Environment, and point a
domain at service `redeemer`, port `8787`. That file is the same stack without a published port,
joined to `dokploy-network` so Traefik can route to it and issue the certificate.

### Without Docker

Python 3.11+ and no dependencies:

```
REDEEMER_ADMIN_PASSWORD=secret python3 -m redeemer serve
```

## Connect an app

Register the app in the panel, then have it POST to `/v1/redeem`. The full contract — every
rejection reason, what to do with each, and what to store on the device — is in
[docs/INTEGRATION.md](docs/INTEGRATION.md).

## Design decisions

**A grant is local and permanent.** When `granted` is true, the app stores it on the device and
never asks again. Disabling a code stops new redemptions; it does not revoke old ones. The
alternative — revalidating periodically — means a server outage or a flight without signal takes
premium away from someone who has it. That trade is not worth making.

**Uses are counted per `(code, app, device)`, not with a counter.** A retry after a dropped
connection returns `already` and spends nothing, so a flaky network can never burn a single-use
code. Anonymous redemptions get the same protection from a short-lived nonce instead.

**No fallback code in the binary.** It would be the one code you could never disable.

**The request IP is never stored.** It feeds the rate limiter in memory and is dropped. Storing
data the panel does not show would be collecting for nothing.

**Nothing here is a secret.** The codes live in a database you control; the app ships no key.
Redemption is rate limited per IP and per device, which is the only protection guessing needs.

## Privacy

A redemption sends the code, the app slug, and either a device UUID your app generates or a
one-shot nonce, plus whatever optional context you choose to send (platform, app version,
country). The server keeps exactly that. No advertising ID, no account, no email, no IP log, no
third party.

**Anonymous mode** stores nothing that identifies anyone: a row saying a code was redeemed at a
time. The nonce that makes retries safe lives in memory for ten minutes and is never written to
disk, which is what Apple and Google mean by data serviced in real time rather than collected.
An app that declares *Data Not Collected* can keep declaring it.

**Identified mode** sends a stable identifier, so it has to be declared:

- **App Store** — Identifiers → Device ID, linked to the user, purpose *App Functionality*. The
  [optional-disclosure exception](https://developer.apple.com/app-store/app-privacy-details/)
  does not cover it: the code is typed by the user, but the UUID is attached automatically.
- **Google Play** — Data safety → Device or other IDs, collected, purpose *App functionality*.
- **GDPR** — a device UUID is personal data. One line in your privacy policy naming the server
  and its purpose is enough; you are the controller and you own the box.

What you trade for the label is reliability of single-use codes: without the UUID a reinstall
redeems again and spends another use. [docs/INTEGRATION.md](docs/INTEGRATION.md) compares both.

Sending `platform`, `app_version` and `country` is optional in either mode. Skip them and the
panel simply shows fewer stats.

Note that a reverse proxy in front of Redeemer usually writes its own access log with client
IPs. That is outside this project, and worth checking if you want the claim to hold end to end.

## Data

Everything lives in `/data`: `redeemer.db` and `backups/`. The server writes a consistent
compressed snapshot daily and keeps the last `REDEEMER_BACKUP_KEEP`. A snapshot on demand:

```
docker compose exec redeemer python -m redeemer backup
```

Moving to another host is one file. Copy `redeemer.db` into the new volume and start. Redemptions
already granted are unaffected by downtime — they live on the device.

## Configuration

| Variable | Default | |
|---|---|---|
| `REDEEMER_ADMIN_PASSWORD` | — | Panel password. Required. |
| `REDEEMER_DB` | `/data/redeemer.db` | |
| `REDEEMER_HOST` / `REDEEMER_PORT` | `0.0.0.0` / `8787` | |
| `REDEEMER_BEHIND_PROXY` | `1` in Docker | Trust `X-Forwarded-For`, mark the session cookie `Secure`. |
| `REDEEMER_BACKUP_DIR` | `/data/backups` | |
| `REDEEMER_BACKUP_KEEP` | `14` | Snapshots kept. |
| `REDEEMER_BACKUP_HOURS` | `24` | Snapshot interval. `0` disables it. |

## Development

```
python3 -m unittest discover -s tests -t .
```

## License

MIT
