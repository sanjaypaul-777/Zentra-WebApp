# BrandBoxWeb (Django)

Public marketing site + account dashboard for **BrandBox**.

This is a **separate** app from the Shopify embedded app in `../BrandBoxApp` (Node).

| Surface | Role | Typical URL |
|---------|------|-------------|
| **Marketing** (this repo) | Landing, login, signup, checkout | `brandbox.co` |
| **Dashboard** (this repo) | After login — connect → build → finder → imports | `app.brandbox.co` |
| **Admin** (this repo) | Staff editor — vault, Product Hunter, users | `/admin/` |
| **BrandBox** (sibling Node) | Shopify OAuth, Admin API, push, live store | Cloudflare tunnel / deploy |

They share **one Shopify Partner app**. In production they should share **one Postgres**; local Django defaults to SQLite.

## How folders work

| Layer | Folder | Job |
|-------|--------|-----|
| **Routes + logic** | `apps/` | `views.py`, `urls.py`, models, services |
| **HTML** | `templates/` | What the user sees |
| **CSS / JS / images** | `static/` | Look & client behavior |
| **Settings + Node client** | `config/` | Django settings, Shopify helpers, `brandbox_client` |

**Rule:** change copy in `templates/…`. Change behavior in `apps/…`. Talk to Node only via `config/brandbox_client.py`.

**CSS rule (page → section → block):** do not style pages from `base.css`. Each page loads its own file; every section uses a unique class prefix so changing one block does not affect another page.

| Page | CSS file | Section prefixes |
|------|----------|------------------|
| Homepage | `static/css/home.css` | `.brandbox-hero*`, `.brandbox-nav*`, … |
| Login / signup | `static/css/auth.css` | `.auth-page`, `.auth-card`, … |
| Dashboard shell | `static/css/dashboard.css` | `.dash`, `.dash-sidebar*`, `.brandbox-btn*` |
| Product Finder / Imports | `static/css/catalog.css` | `.catalog`, finder / import blocks |
| My Stores | `static/css/stores.css` | `.ms-*` |
| Settings | `static/css/settings.css` | `.st-*` |
| Builder | `static/css/builder.css` | `.build-*`, `.ab-*` |
| Checkout | `static/css/checkout.css` | `.checkout*` |
| Contact | `static/css/contact.css` | `.contact-*` |
| 404 / 500 / failed | `static/css/status.css` | `.status-*` |

`base.css` = color names + reset only (~100 lines). Never load `home.css` on dashboard pages.

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
  404 / 500 custom pages (handler404 / handler500 — BBX-500-… refs)
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
> **Errors:** never show raw exceptions to users. 500 pages show a `BBX-500-…`
> reference logged with the real traceback for support.

## Project tree

```text
BrandBoxWeb/
├── manage.py
├── requirements.txt
├── .env.example / .env.local          # secrets gitignored
├── config/
│   ├── settings.py                    # apps, DB, CATALOG_*, SHOPIFY_APP_URL
│   ├── urls.py                        # mounts apps + /admin/
│   ├── shopify.py                     # normalize shop + OAuth URL → Node
│   ├── brandbox_client.py               # all Node internal HTTP (secret header)
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
│   ├── css/                           # page CSS (base + page files)
│   ├── js/
│   └── images/
└── secrets/                           # google-sheets-sa.json (gitignored)
```

## End-to-end workflow

Two separate accounts:

1. **BrandBox login** = this webapp (`User`)
2. **Shopify store** = merchant’s `*.myshopify.com` (connected via Node OAuth)

### Workflow charts

#### Full system (store states)

```mermaid
flowchart TD
  Start([Open BrandBox Web]) --> Auth{BrandBox logged in?}

  Auth -->|No| Login[Signup / Login]
  Login -->|Fail| Login
  Login -->|OK| Dash[/dashboard/]
  Auth -->|Yes| Dash

  Dash --> State{Shopify ↔ BrandBox status}

  State -->|No Shopify account yet| CreateCard[Create Shopify Account]
  CreateCard --> Partner[Shopify signup / free trial]
  Partner --> Back[Come back with *.myshopify.com]
  Back --> ConnectCard

  State -->|Has Shopify store<br/>but NOT connected| ConnectCard[Connect Shopify]
  ConnectCard --> Paste[Paste yourstorename.myshopify.com]
  Paste --> Pending[(DB: ShopConnection<br/>PENDING app_installed=false)]
  Pending --> InstallUI[Install BrandBox guide]

  State -->|Domain saved<br/>pending install| InstallUI
  InstallUI --> OAuth[Redirect → Node OAuth]
  OAuth --> NodeSession[(Node: Shopify Session)]
  NodeSession --> Check[GET /api/install-status]
  Check -->|Not installed| InstallUI
  Check -->|Installed| Active[(DB: ShopConnection<br/>ACTIVE app_installed=true)]
  Active --> Dash

  State -->|Already connected<br/>app_installed=true| Hub{Choose work}

  Hub --> Overview[Overview]
  Hub --> Builder[AI Store Builder]
  Hub --> Finder[Product Finder]
  Hub --> Imports[My Imports]
```

#### Store status meanings

```mermaid
flowchart LR
  A[No Shopify store] --> B[Has Shopify store]
  B --> C[Pending in BrandBox<br/>domain saved only]
  C --> D[Active in BrandBox<br/>OAuth + app installed]

  A -.->|Create account| B
  B -.->|Connect + paste domain| C
  C -.->|Install / OAuth| D
```

| Status | Meaning | What user does |
|--------|---------|----------------|
| **No Shopify store** | Never created a Shopify shop | **Create Shopify Account** |
| **Has store, not connected** | Shop exists, BrandBox doesn’t know it | **Connect** → paste `*.myshopify.com` |
| **Pending** | Domain in DB, `app_installed=false` | **Install BrandBox** (Node OAuth) |
| **Active / connected** | `app_installed=true` | Overview, Builder, Finder Import, Push |

#### AI Store Builder (full flow)

Requires **Active** connection (`app_installed=true`).

```mermaid
flowchart TD
  Hub[Connected shop] --> Builder[/dashboard/builder/]

  Builder --> Niche[Pick niche NichePack]
  Niche --> Opt{Options?}
  Opt --> Start[Start build]

  Start --> Job[(DB WRITE BuildJob<br/>status=running)]
  Job --> Preview{Staff preview shop?}

  Preview -->|Yes admin-preview-*| Sim[Local timed simulator]
  Preview -->|No real shop| NodeStart[Node POST /api/build/start]
  NodeStart --> Eng[(Node build engine<br/>theme + products)]
  Eng --> Building[/builder/building/id/]

  Sim --> Building
  Building --> Poll[Poll Node GET /api/build/status]
  Poll --> Sync[(DB UPDATE BuildJob<br/>progress / label / step)]
  Sync --> Done{Outcome?}

  Done -->|completed| Success[/builder/success/id/<br/>BuildJob=done]
  Done -->|failed| Fail[build_failed UI<br/>BuildJob=failed]
  Done -->|still running| Building

  Fail --> Retry[Retry]
  Retry --> NodeRetry[Node POST /api/build/retry]
  NodeRetry --> Job
```

| Step | Django | Node |
|------|--------|------|
| Pick niche | `NichePack` UI | optional `GET /api/niches` counts |
| Start | create `BuildJob` | `POST /api/build/start` |
| Progress | building page + poll sync | `GET /api/build/status` → theme/products on Shopify |
| Done / fail | success or failed UI | job completed / failed |
| Retry | new/linked `BuildJob` | `POST /api/build/retry` |

#### Overview / Finder / Push

```mermaid
flowchart TD
  Hub{Connected shop} --> OV[Overview]
  Hub --> BD[Builder — see chart above]
  Hub --> PF[Product Finder]
  Hub --> MI[My Imports]

  OV --> OV1[(Read jobs + connection)]
  OV --> OV2[Node: product count]

  PF --> PF1[(Read CatalogProduct)]
  PF --> PF2{Import?}
  PF2 -->|Yes| PF3[(Write ShopImport)]

  MI --> MI1{Edit / Remove / Push}
  MI1 -->|Push| MI2[Node: create + publish]
  MI2 --> MI3[(ShopImport in_store)]
```

#### Product Hunter → vault (staff)

```mermaid
flowchart TD
  H[Admin hunt] --> L{404?}
  L -->|Yes| S([Skip])
  L -->|No| U[USD prices]
  U --> V[(CatalogProduct)]
  U --> G[Sheet]
```

#### Who owns what

```mermaid
flowchart LR
  subgraph BrandBoxWeb[Django webapp]
    User
    ShopConnection
    CatalogProduct
    ShopImport
    BuildJob
  end

  subgraph BrandBoxNode[Node app]
    OAuth
    Session
    Build
    Publish
  end

  subgraph ShopifyCloud[Shopify]
    Store
  end

  User -->|login| ShopConnection
  ShopConnection -->|install-status| OAuth
  OAuth --> Session
  Session --> Store
  BuildJob --> Build --> Store
  ShopImport -->|push| Publish --> Store
  CatalogProduct --> ShopImport
```

---

### Who owns what (tables)

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

Django **never** stores Shopify Admin access tokens. It calls Node with `X-BrandBox-Internal-Secret`.

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
     → DB WRITE BuildJob (status running, brandbox_build_id=…)
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

### 8) Node API map (Django → BrandBox)

All via `config/brandbox_client.py` + header `X-BrandBox-Internal-Secret`.  
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
| Server error | `BBX-500-…` page | Traceback only in logs |

## Local setup

```bash
cd BrandBoxWeb
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
BRANDBOX_INTERNAL_API_SECRET=brandbox-dev-shared-secret
CATALOG_SPREADSHEET_ID=...
CATALOG_SHEET_TAB=Meta Ads Products
```

Refresh `SHOPIFY_APP_URL` whenever `../BrandBoxApp` → `npm run dev` prints a new Cloudflare URL.

### Shared database (production)

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/brandbox
```

Use the **same** Postgres as BrandBox when you want shared users/shops. Local default is SQLite (`db.sqlite3`).

## Useful CLI (catalog)

```bash
python manage.py scrape_products -q skincare -c US -n 30
python manage.py scrape_products --sync-sheet
python manage.py scrape_products --clean-prices   # Sheet 12000 → 120.00
python manage.py scrape_products --purge-dead     # drop 404 vault rows
```

## Next steps

1. Real password-reset email + Google / Apple / Facebook OAuth
2. Celery worker for long Product Hunter / builds
3. Shared Postgres with BrandBox in staging/prod
4. Surface Node publish warnings (stock/scopes) clearly in My Imports toasts
