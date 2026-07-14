# Zentra-Web (Django)

Public marketing site + account dashboard for **Zentra**.

This is a **separate** app from the Shopify embedded app in `../Zentra` (Node).

| Surface | Role | Typical URL |
|---------|------|-------------|
| **Marketing** (this repo) | Landing, login, signup, checkout | `zentra.com` |
| **Dashboard** (this repo) | After login — connect → build → finder → imports | `app.zentra.com` |
| **Admin** (this repo) | Staff editor — vault, Product Hunter, users | `/admin/` |
| **Zentra** (sibling Node) | Shopify OAuth, Admin API, push, live store | Cloudflare tunnel / deploy |

They share **one Shopify Partner app**. In production they should share **one Postgres**; local Django defaults to SQLite.

## How folders work

| Layer | Folder | Job |
|-------|--------|-----|
| **Routes + logic** | `apps/` | `views.py`, `urls.py`, models, services |
| **HTML** | `templates/` | What the user sees |
| **CSS / JS / images** | `static/` | Look & client behavior |
| **Settings + Node client** | `config/` | Django settings, Shopify helpers, `zentra_client` |

**Rule:** change copy in `templates/…`. Change behavior in `apps/…`. Talk to Node only via `config/zentra_client.py`.

## Who can see what

```text
PUBLIC
  /                         marketing landing
  /checkout/                purchase (optional account)
  /login/ /signup/ /forgot/

AFTER LOGIN
  /dashboard/               Overview (stores built + live product count)
  /dashboard/connect/       paste *.myshopify.com → install guide
  /dashboard/install/       redirect to Node OAuth
  /dashboard/builder/       AI Store Builder niche wizard
  /builder/building/<id>/   build progress
  /builder/success/<id>/    build success
  /dashboard/product-finder/  Winning Product Vault browse + Import
  /dashboard/imports/         My Imports edit / remove / Push
  /dashboard/stores/          My Stores
  /dashboard/settings/        account + prefs

STATUS / ERRORS
  404 / 500 custom pages (handler404 / handler500 — ZEN-500-… refs)
  Maintenance via MAINTENANCE_MODE + MAINTENANCE_ETA
  DEBUG previews: /__debug__/404/ · /__debug__/500/ · /__debug__/maintenance/

STAFF / SUPERUSER
  /admin/                   users, ShopConnection, NichePack, BuildJob
  /admin/ … Product Hunter  ScrapeRun — hunt / sync / purge-dead / clean-prices
  /admin/ … Winning Product Vault  CatalogProduct rows
```

> **Product Finder** reads Django SQL (`CatalogProduct`). **My Imports** are shop drafts
> (`ShopImport`). **Push to Shopify** calls the Node app (Admin token stays in Node).
>
> **Errors:** never show raw exceptions to users. 500 pages show a `ZEN-500-…`
> reference logged with the real traceback for support.

## Project tree

```text
Zentra-Web/
├── manage.py
├── requirements.txt
├── .env.example / .env.local          # secrets gitignored
├── AGENTS.md / CLAUDE.md
├── config/
│   ├── settings.py                    # apps, DB, CATALOG_*, SHOPIFY_APP_URL
│   ├── urls.py                        # mounts apps + /admin/
│   ├── shopify.py                     # normalize shop + OAuth URL → Node
│   ├── zentra_client.py               # all Node internal HTTP (secret header)
│   ├── middleware.py / context_processors.py
│   ├── celery.py                      # reserved for long builds
│   └── wsgi.py / asgi.py
├── apps/
│   ├── home/                          # landing /
│   ├── accounts/                      # login, signup, logout, forgot
│   ├── dashboard/                     # Overview, Connect, Finder, Imports, Stores
│   │   ├── models.py                  # ShopConnection, UserPlan, ActivityEvent
│   │   ├── catalog.py                 # search_vault() → CatalogProduct
│   │   ├── overview.py                # Overview stats + Node product count
│   │   ├── views.py                   # pages + /dashboard/api/*
│   │   └── urls.py
│   ├── builder/                       # AI Store Builder (web job + Node engine)
│   │   ├── models.py                  # NichePack, BuildJob
│   │   ├── niches.py                  # niche metadata + Node niche sync
│   │   ├── services.py                # start/poll/retry remote build
│   │   ├── wizard.py / views.py
│   │   └── urls.py                    # /builder/*
│   ├── catalog/                       # vault + imports + Product Hunter
│   │   ├── models.py                  # CatalogProduct, ShopImport, ScrapeRun
│   │   ├── services/
│   │   │   ├── dual_write.py          # Sheet ↔ CatalogProduct
│   │   │   ├── imports.py             # create/list/push ShopImport
│   │   │   ├── money.py               # FX → USD, Shopify cents fix
│   │   │   ├── pipeline.py            # hunt / sync / clean-prices / purge
│   │   │   └── validate.py            # 404 skip/purge
│   │   ├── scraper/                   # Meta Ads + Shopify page scrape
│   │   └── management/commands/scrape_products.py
│   └── checkout/                      # public checkout UI
├── templates/
│   ├── accounts/  home/  checkout/
│   ├── dashboard/                     # overview, connect, finder, imports…
│   ├── builder/                       # building, success, failed
│   └── admin/catalog/scraperun/       # Start Hunting UI
├── static/
│   ├── css/                           # design tokens + page CSS
│   ├── js/                            # product-finder.js, my-imports.js…
│   └── images/
├── secrets/                           # google-sheets-sa.json (gitignored)
└── docs/
    ├── Workflow.md                    # full flowcharts (auth → push)
    ├── WEBAPP-SHOPIFY-INTEGRATION.md
    ├── Catalog-scraper.md
    ├── UI-Design-System.md
    └── copy.md
```

## End-to-end workflow

**Workflow charts (diagrams only):** [`docs/Workflow.md`](docs/Workflow.md)

Who owns what:

| Concern | Owner | Storage |
|---------|--------|---------|
| User account | Django | `auth.User` |
| Shop link (pending / installed) | Django | `ShopConnection` |
| Winning products catalog | Django (+ Sheet dual-write) | `CatalogProduct` |
| My Imports drafts | Django | `ShopImport` |
| Build job / niche UI records | Django | `BuildJob`, `NichePack` |
| Shopify OAuth + Admin token | **Node only** | Prisma `Session` |
| Create / publish products to store | **Node only** | Shopify Admin API |
| Theme build engine | **Node** | Prisma build + Admin API |

Django **never** stores Shopify Admin access tokens. It calls Node with `X-Zentra-Internal-Secret`.

---

### 1) Authentication (Django only)

```text
Browser → /signup/ or /login/
        → apps/accounts (Django auth.User)
        → success → /dashboard/
        → fail → same form with errors

/forgot/     → UI placeholder (no email send yet)
/logout/     → home
/oauth/<p>/  → stub message (Google/Apple/FB not wired)
```

**DB write:** `User` on signup.  
**DB read:** session user on every `@login_required` page.  
**Node:** not involved.

---

### 2) Connect store → OAuth → install confirmed

```text
1. User opens /dashboard/connect/
2. Pastes brand.myshopify.com
3. Django saves ShopConnection (app_installed=False)  ← DB WRITE pending
4. User clicks Install → /dashboard/install/
5. Django redirects browser to:
     {SHOPIFY_APP_URL}/auth/login?shop=brand.myshopify.com
6. Node runs Shopify OAuth → saves Prisma Session (token stays in Node)
7. Browser returns to /dashboard/?shop=...
8. Django calls Node GET /api/install-status?shop=...
9. If installed:true → ShopConnection.app_installed=True  ← DB WRITE active
   (+ caches store_product_count)
10. Success → Overview / Builder unlock
    Fail → /dashboard/connect/error/ or retry Install
```

**Poll while waiting:** browser → `GET /dashboard/api/install-status/` → Django → Node `GET /api/install-status`.

**Pending vs active:** only `app_installed=True` counts as connected. Pending rows must not unlock Builder / Overview “connected” stats.

**Staff preview:** superuser without a real shop may get `admin-preview-*.myshopify.com` so Builder UI can be tested (no live Shopify product count).

---

### 3) Overview

```text
/dashboard/
  DB READ  ShopConnection.active_for_user
  DB READ  BuildJob DONE count for that shop  → “stores built”
  API      Node GET /api/install-status         → live product count
           (cached ~90s on ShopConnection.store_product_count)
```

If Node/tunnel is down → show “product count unavailable”, never invent `0`.

---

### 4) AI Store Builder

```text
1. /dashboard/builder/  pick niche (NichePack from DB; counts may sync from Node GET /api/niches)
2. Start build → apps/builder/services.py
     → Node POST /api/build/start
     → DB WRITE BuildJob (status running, zentra_build_id=…)
3. /builder/building/<id>/ polls:
     → Node GET /api/build/status
     → DB UPDATE BuildJob progress / status
4. Success → /builder/success/<id>/   (BuildJob.status=done)
   Fail    → build_failed UI
   Retry   → Node POST /api/build/retry → new/linked job
```

**Staff preview shops:** may use a local timed simulator instead of Node.  
**Real shops:** theme/product upload runs in Node; webapp owns the guided UI + job rows.

---

### 5) Product Hunter → Winning Product Vault (admin / CLI)

Staff fills the catalog (not the merchant UI):

```text
/admin/ Product Hunter (ScrapeRun)  or  manage.py scrape_products
  → Meta Ads landing pages → Shopify product scrape
  → 404 guard: skip dead product URL / images (not stored)
  → money: detect FX → convert to USD; fix Shopify cents (12000→120.00)
  → DB WRITE CatalogProduct
  → Google Sheet append/update (Node sheet dual-write / ops)

Other modes:
  --sync-sheet     Sheet → DB (skips dead)
  --clean-prices   rewrite Sheet Price/Compare to USD dollars
  --purge-dead     delete vault rows with dead sources/images
  --clean-dupes / --fill-ids
```

**Merchant Product Finder never reads the Sheet.** It reads `CatalogProduct` SQL only.

---

### 6) Product Finder → Import draft

```text
1. /dashboard/product-finder/
2. DB READ CatalogProduct via search_vault() (q / country / niche / page)
3. Import click → POST /dashboard/api/imports/
     → DB WRITE ShopImport (status=imported) for this shop+sourceId
     → cost/sell/compare from vault (USD); sell default = cost × 3
4. Badges: already imported / in_store from ShopImport rows for this shop

Node: not called for browse. Connect a real shop to Import (preview can browse only).
```

---

### 7) My Imports → edit → Push to Shopify

```text
List  /dashboard/imports/
  DB READ ShopImport for connected shop
  optional Node GET /api/imports → sync in_store / removed_from_store

Edit  PATCH /dashboard/api/imports/<id>/
  DB WRITE title / sell / compare / cost (local only)

Remove DELETE /dashboard/api/imports/<id>/
  DB DELETE ShopImport only  (CatalogProduct vault kept)

Push  POST … action=publish
  1) Node POST /api/imports          (upsert PendingProduct + prices + source URL)
  2) Node POST /api/imports/:id/publish  (Shopify productCreate + price/stock/channels)
  3) On success: DB WRITE ShopImport status=in_store, shopify_product_id=…
  Fail toast if Node/tunnel down or publish errors
```

**Success path:** toast “Pushed”, row leaves “imported” queue (`in_store`).  
**Error path:** toast with Node message; draft stays editable.

---

### 8) Node API map (Django → Zentra)

All via `config/zentra_client.py` + header `X-Zentra-Internal-Secret`.  
Base URL = `SHOPIFY_APP_URL` (update when Cloudflare tunnel changes).

| When | Django helper | Node |
|------|---------------|------|
| After OAuth / Overview / install poll | `check_app_installed` | `GET /api/install-status` |
| Niche product counts / themes | `fetch_niches` | `GET /api/niches` |
| Start AI build | `start_remote_build` | `POST /api/build/start` |
| Poll build | `get_remote_build_status` | `GET /api/build/status` |
| Retry build | `retry_remote_build` | `POST /api/build/retry` |
| Sync live import statuses | `list_imports` | `GET /api/imports` |
| Push prep | `create_import` | `POST /api/imports` |
| Push live | `publish_import` | `POST /api/imports/:id/publish` |

---

### 9) Success & error summary

| Step | Success | Failure |
|------|---------|---------|
| Signup/Login | Session + `/dashboard/` | Form errors |
| Connect | Pending `ShopConnection` | Invalid domain / owned by other user |
| OAuth / install | `app_installed=True` | Connect error page; tunnel/secret wrong |
| Builder | `BuildJob` done + success page | Failed page + retry |
| Finder browse | Vault cards | Empty / connect banner for Import |
| Import | `ShopImport` created | Not in vault / no shop |
| Push | `in_store` + Shopify product | Toast: Node/tunnel/publish error |
| Server error | `ZEN-500-…` page | Traceback only in logs |

## Local setup

```bash
cd Zentra-Web
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env.local
python manage.py migrate
python manage.py createsuperuser   # for /admin/
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Set in `.env.local`:

```env
SHOPIFY_APP_URL=https://YOUR-TUNNEL.trycloudflare.com
ZENTRA_INTERNAL_API_SECRET=zentra-dev-shared-secret
CATALOG_SPREADSHEET_ID=...
CATALOG_SHEET_TAB=Meta Ads Products
```

Refresh `SHOPIFY_APP_URL` whenever `../Zentra` → `npm run dev` prints a new Cloudflare URL.

### Shared database (production)

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/zentra
```

Use the **same** Postgres as Zentra when you want shared users/shops. Local default is SQLite (`db.sqlite3`).

## Useful CLI (catalog)

```bash
python manage.py scrape_products -q skincare -c US -n 30
python manage.py scrape_products --sync-sheet
python manage.py scrape_products --clean-prices   # Sheet 12000 → 120.00
python manage.py scrape_products --purge-dead     # drop 404 vault rows
```

See `docs/Catalog-scraper.md` and `docs/WEBAPP-SHOPIFY-INTEGRATION.md`.

## Next steps

1. Real password-reset email + Google / Apple / Facebook OAuth
2. Celery worker for long Product Hunter / builds
3. Shared Postgres with Zentra in staging/prod
4. Surface Node publish warnings (stock/scopes) clearly in My Imports toasts
