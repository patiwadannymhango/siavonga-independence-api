# Siavonga Independence Run 2026 — Backend API

A single-event Django REST API for the Siavonga Independence Run 2026
registration site
([siavonga-inpendence-run-2026-site](../siavonga-inpendence-run-2026-site)).
Built from the same pattern as a larger multi-tenant event platform, but
trimmed down to exactly what this one event needs — no organizations, no
multi-event membership/roles, no Celery/Redis. Two race categories, one
registration form, one payment flow.

```
siavonga-independence-api/
├── backend/                   Django REST API
├── docker-compose.yml         local development
├── docker-compose.prod.yml    production (backend + Postgres + Caddy)
├── Caddyfile                  reverse proxy in front of the backend
└── .github/workflows/deploy.yml
```

## What's here

- **Race categories** — 10KM Competitive Run (K300) and 5KM Fun Run &
  Walk (K250), seeded automatically. Managed in Django admin
  (`/django-admin/`) or via `python manage.py seed_categories`.
- **Registration** — a runner submits their details once; a
  `Participant` + `Registration` pair is created `PENDING_PAYMENT`.
- **Payments** — mobile money (MTN/Airtel/Zamtel), card, or bank
  transfer, via a pluggable gateway:
  - **`console`** (default) — no credentials needed. Simulates a
    payment settling ~5 seconds after being initiated, so the full
    registration → pay → poll → confirmed flow works locally out of the
    box.
  - **`lipila`** — the real Zambian payment gateway. Switch by setting
    `PAYMENT_GATEWAY=lipila` and filling in the `LIPILA_*` keys in
    `backend/.env` once you have sandbox/production credentials.
- **Notifications** — SMS on registration received / payment
  confirmed / payment failed, one email on confirmation. SMS defaults to
  a `console` backend (logs instead of sending — see
  `apps/notifications/sms.py` to wire up Africa's Talking later). Email
  defaults to Django's console backend in dev, real SMTP in production.
- **Admin** — Django's built-in admin site at `/django-admin/` (full
  CRUD over categories, registrations, payments, notifications) plus a
  small JWT-authenticated admin API (`/api/v1/admin/...`) for a future
  dashboard: registration list/search/export, manual walk-in
  registration, bulk CSV/XLSX upload, dashboard stats.

## API surface

Public (no auth), consumed directly by the registration site:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/categories/` | Race categories + prices |
| POST | `/api/v1/registrations/` | Create a registration |
| GET | `/api/v1/registrations/lookup/?q=` | "Track your registration" by reference or email |
| POST | `/api/v1/payments/initiate/` | Start mobile money / card / bank transfer payment |
| GET | `/api/v1/payments/<id>/status/` | Poll payment status |
| POST | `/api/v1/payments/webhooks/lipila/` | Lipila's server-to-server callback |
| GET | `/api/v1/payments/bank-details/` | Bank account details for bank transfer |

Admin (JWT, staff account required) under `/api/v1/auth/...` and
`/api/v1/admin/...` — see `backend/apps/*/urls.py` for the full list.

## Running locally

Requires Docker Desktop.

```bash
cp backend/.env.example backend/.env   # defaults work as-is for local dev
docker compose up -d --build
```

This starts Postgres and the Django dev server (hot-reload) on
`http://localhost:8001` (port 8001, not 8000 — avoids clashing with
another Django project's dev container that might already be using 8000
on this machine; change it back in `docker-compose.yml` if that's not a
concern for you). On first boot the entrypoint runs migrations and seeds
the two race categories automatically.

Create an admin login (for `/django-admin/` and the admin API):

```bash
docker compose exec backend python manage.py createsuperuser
```

Confirm it's up:

```bash
curl http://localhost:8001/api/v1/categories/
```

Point the frontend at it — in
`siavonga-inpendence-run-2026-site/.env`:

```
VITE_API_BASE_URL=http://localhost:8001
```

### Running without Docker

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # set DB_HOST=localhost and point at a local Postgres
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
python manage.py runserver
```

## Testing payments locally

With the default `PAYMENT_GATEWAY=console`, no real money or credentials
are involved: initiate a payment, then poll
`/api/v1/payments/<id>/status/` — it flips from `PROCESSING` to
`SUCCESS` on its own about 5 seconds after creation (see
`apps/payments/gateways/console.py`), which also flips the registration
to `CONFIRMED` and sends the confirmation email/SMS.

Bank transfer skips the gateway entirely — the registration goes to
`PAYMENT_PROCESSING` immediately, and an admin manually flips it to
`CONFIRMED` (via `/django-admin/` or `PATCH
/api/v1/admin/registrations/<id>/`) once the transfer is reconciled
against the bank statement.

## Switching on real Lipila payments

1. Get sandbox (then production) API keys and a webhook secret from
   Lipila.
2. In `backend/.env`: `PAYMENT_GATEWAY=lipila`, `LIPILA_ENVIRONMENT=sandbox`,
   `LIPILA_SANDBOX_API_KEY=...`, `LIPILA_WEBHOOK_SECRET=...`.
3. Point Lipila's webhook URL at
   `http://<your-address>/api/v1/payments/webhooks/lipila/`. Lipila
   calls this from the internet, so it only works once the backend is
   reachable from outside — a laptop on `localhost` never receives
   webhooks. Registration, the payment status poll, and payment
   *initiation* all still work locally either way; only the webhook
   *confirmation* needs a public address. For local webhook testing, put
   a tunnel (ngrok, cloudflared) in front of the backend and use the
   tunnel's URL here.
4. Restart the backend so the new env vars take effect.

Note: Lipila's docs describe two API generations (a legacy `x-api-key` /
`/api/v1/collections/...` surface and a newer Bearer-token surface). The
client in `apps/payments/gateways/lipila/client.py` is built against the
older style — confirm against your Lipila merchant dashboard which one
you were issued, and adjust if needed.

## Deploying

This repo deploys the same way regardless of address — a laptop, a LAN
IP, or a cloud server's public IP, all work identically since nothing
here depends on a domain existing yet.

**1. Push to GitHub, then on the server:**

```bash
git clone <this-repo-url>
cd siavonga-independence-api
cp .env.prod.example .env.prod          # set DB password; leave HTTP_PORT=80
cp backend/.env.example backend/.env    # set DEBUG=False, a real SECRET_KEY,
                                          # DJANGO_SETTINGS_MODULE=config.settings.production,
                                          # DB credentials matching .env.prod,
                                          # and ALLOWED_HOSTS listing every address
                                          # you'll reach the API by
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Confirm it's up: `curl http://<server-address>/api/v1/categories/`.

**2. HTTPS (needed once a real frontend deploy calls this over the
internet — browsers block an HTTPS page from calling plain `http://`).**
No domain purchase required — with a fixed IP, `<ip-with-dashes>.sslip.io`
is a real, publicly resolvable hostname Caddy can fetch a genuine Let's
Encrypt cert for automatically:

```
# in .env.prod
SITE_ADDRESS=https://15-240-170-199.sslip.io
```

(swap in a real domain later by pointing an A record at the same IP and
changing this one line). Then:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --force-recreate proxy
```

Add the hostname to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in
`backend/.env` too.

**3. Point the frontend at it** — set `VITE_API_BASE_URL` to the
server's address in whatever host serves the frontend, and add that
frontend's real domain to `CORS_ALLOWED_ORIGINS` in `backend/.env`, then:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --force-recreate backend
```

**4. Automatic redeploy on push** — `.github/workflows/deploy.yml` SSHes
into the server and rebuilds on every push to `main`. Add these repo
secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `SERVER_HOST` | server's public IP or hostname |
| `SERVER_SSH_USER` | SSH user (e.g. `ubuntu`) |
| `SERVER_SSH_PRIVATE_KEY` | a dedicated deploy key's private key (not your personal one) |
| `SERVER_PROJECT_PATH` | absolute path to the repo on the server |

**5. Database backups** — `infra/backup-db.sh` / `infra/restore-db.sh`
handle daily dumps (local + optional offsite S3). One-time setup and
cron wiring in [`infra/README.md`](infra/README.md) — set this up before
there are real registrations to lose.

I'll help fill in the specific server/domain/Lipila details when you're
ready to deploy — just share them when you get there.
