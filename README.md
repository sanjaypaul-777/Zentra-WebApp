# BrandBoxWeb (Django)

Public marketing site + account dashboard for **BrandBox**.

This is a **separate** app from the Shopify embedded app in `../BrandBoxApp` (Node).

| Surface | Role | Typical URL |
|---------|------|-------------|
| **Marketing** (this repo) | Landing, affiliate, Help Center, legal, login, signup, checkout | `brandbox.co` |
| **Dashboard** (this repo) | After login — connect → builder → vault → imports → coach | `app.brandbox.co` |
| **Admin** (this repo) | Staff editor — vault, Product Hunter, Help, Coach profiles | `/admin/` |
| **BrandBox** (sibling Node) | Shopify OAuth, Admin API, push, live store | Cloudflare tunnel / deploy |

They share **one Shopify Partner app**. In production they should share **one Postgres**; local Django defaults to SQLite.

**Display knobs** (offer %, affiliate %, coach copy): edit only [`config/product.py`](config/product.py). Deploy notes: [`docs/DEPLOY.md`](docs/DEPLOY.md).

## How folders work

| Layer | Folder | Job |
|-------|--------|-----|
| **Routes + logic** | `apps/` | `views.py`, `urls.py`, models, services |
| **HTML** | `templates/` | What the user sees |
| **CSS / JS / images** | `static/` | Look & client behavior |
| **Settings + Node client** | `config/` | Django settings, Shopify helpers, `brandbox_client` |

**Rule:** change copy in `templates/…`. Change behavior in `apps/…`. Talk to Node only via `config/brandbox_client.py`.

**CSS rule (page → section → block):** `base.css` `:root` is **shared primitives only** (body, cards, buttons, brand accents, fonts). Never restyle one page from `:root`. Each page/section owns `--prefix-*` tokens on its root class — change those, and only that section updates. **Sizing units are px only** (no rem/em) across CSS, Tailwind theme, and inline styles.

| Page | CSS file | Section root → tokens |
|------|----------|----------------------|
| Homepage | `static/css/home.css` | `.brandbox-home` → `--home-*`; `.brandbox-hero` → `--hero-*` |
| Affiliate landing | `static/css/affiliate.css` (+ `home.css` footer) | `.brandbox-affiliate-page` → `--aff-*` |
| Help Center | `static/css/help.css` (+ `home.css` footer) | `.help-page` → `--help-*` |
| Login / signup / legal shell | `static/css/auth.css` | `.auth-page` → `--auth-*` |
| Legal (privacy / terms / refund / disclaimer / about) | `static/css/legal.css` | `.legal-page` → `--legal-*` |
| Dashboard shell | `static/css/dashboard.css` | `.dash` → `--dash-*`; `.dash-sidebar` → `--sidebar-*` |
| Overview / Connect / Coach | `static/css/dashboard.css` | `.ov` → `--ov-*`; `.nc` → `--nc-*`; `.ov-coach` / `.coach-kb` |
| Product Hunter / Imports | `static/css/catalog.css` | `.catalog` → `--cat-*` |
| My Stores | `static/css/stores.css` | `.ms` → `--ms-*` |
| Settings | `static/css/settings.css` | `.st` → `--st-*` |
| Onboarding | `static/css/onboarding.css` | `.ob` → `--ob-*` |
| Builder | `static/css/builder.css` | `.ab` → `--ab-*`; `.build-page` → `--build-*` |
| Checkout | `static/css/checkout.css` | `.checkout` → `--checkout-*` |
| Contact | `static/css/contact.css` | `.contact-page` → `--contact-*` |
| 404 / 500 / failed | `static/css/status.css` + `auth.css` | Auth shell (`.auth-page`); status content/buttons |

Example: left panel background → `--sidebar-bg` on `.dash-sidebar` in `dashboard.css`. Shared `.brandbox-btn` keeps using bridged `--primary` from the nearest section.

## Who can see what

```text
PUBLIC
  /                         marketing landing (CTAs → dashboard builder / vault / coach)
  /affiliate/               affiliate program landing
  /affiliate/register/      affiliate partner signup
  /help/                    Help Center (browse topics + search)
  /help/<category>/         topic / category
  /help/<category>/<slug>/  article (+ feedback POST)
  /contact/                 contact form
  /about/                   about us
  /privacy/                 privacy policy
  /terms/                   terms of service
  /refund/                  refund policy
  /disclaimer/              disclaimer
  /newsletter/              newsletter subscribe (POST)
  /checkout/                purchase (optional account)
  /login/ /signup/ /forgot/
  /oauth/<provider>/        social auth start (google, …)

AFTER LOGIN (merchants)
  /onboarding/              required once — 4-step store setup (gates dashboard)
  /password/change/         change password
  /logout/                  end session
  /dashboard/               Overview (stores built + live product count)
  /dashboard/connect/       paste *.myshopify.com → install guide
  /dashboard/create-store/  create store guide
  /dashboard/install/       redirect to Node OAuth
  /dashboard/builder/       AI Store Builder niche wizard
  /dashboard/builder/start/ start build job
  /dashboard/builder/building/<id>/   build progress
  /dashboard/builder/success/<id>/    build success
  /dashboard/product-hunter/  Product Vault browse + Import (?picks=1 = AI Picks)
  /dashboard/imports/         My Imports edit / remove / Push
  /dashboard/stores/          My Stores
  /dashboard/stores/<id>/     store detail
  /dashboard/coach/           BrandBox Coach chat (+ Help shortcuts)
  /dashboard/coach/api/…      coach session / send / request-coach / close
  /dashboard/schedule/        live clock + call booking calendar
  /dashboard/training/        on-demand lessons
  /dashboard/settings/        account + prefs
  /dashboard/settings/profile/  edit profile (same fields as onboarding)
  /dashboard/upgrade/         upgrade / plans

COACH STAFF (CoachProfile.is_coach + staff)
  /dashboard/coach-desk/      live coach inbox / claim / reply / reassign
  /dashboard/coach-desk/api/… desk state + session actions

STATUS / ERRORS
  404 / 500 custom pages (handler404 / handler500 — BBX-500-… refs)
  Maintenance via MAINTENANCE_MODE + MAINTENANCE_ETA
  DEBUG previews: /404/ · /500/ · /__debug__/404/ · /__debug__/500/ · /__debug__/maintenance/
  (With DEBUG=True, unknown URLs show Django’s yellow page — not the custom template)

STAFF / SUPERUSER (development)
  Bypass onboarding gate — open any /dashboard/* URL
  /onboarding/?step=1…4     preview any step anytime
  /dashboard/builder/building/<id>/   open any build job (not only own)
  /dashboard/imports/       preview shop allowed for staff QA
  /admin/                   full CRUD (profiles, shops, jobs, vault, Help, Coach, …)
```

> **Product Hunter / Vault** reads Django SQL (`CatalogProduct`). **My Imports** are shop
> drafts (`ShopImport`). **Push to Shopify** calls the Node app (Admin token stays in Node).
>
> **Help Center** is public (`apps/help`). Seed with `python manage.py seed_help` or
> `loaddata backups/help_knowledge_base.json`. **Coach** (`apps/coach`) is AI-first chat;
> live coach transfer is plan-gated (`UserPlan.is_pro`). Enable coaches in Admin
> (`CoachProfile`).
>
> **Homepage CTAs** (Build / Explore vault / Start with coach / chat Send) go to
> `/dashboard/builder/`, `/dashboard/product-hunter/`, and `/dashboard/coach/` — login
> (and plan checks) apply on those routes as usual.
>
> **Errors:** never show raw exceptions to users. 500 pages show a `BBX-500-…`
> reference logged with the real traceback for support.
>
> **Superadmin / staff (dev):** `is_staff` or `is_superuser` can view and walk **any**
> product URL and wizard step without merchant gates. Create with
> `python manage.py createsuperuser`. Prefer `/admin/` to edit other users’ data.

## URL flow (step · status · error)

Merchant journey URLs — use this as the product flow checklist.

| URL | Step | Status (happy path) | Error / blocked |
|-----|------|---------------------|-----------------|
| `/` | Marketing | Landing loads; CTAs → builder / vault / coach | — |
| `/affiliate/` | Affiliate | Program landing + commission copy | — |
| `/affiliate/register/` | Affiliate signup | Partner registration | Validation |
| `/help/` | Help Center | Topics + search | Empty KB until seeded |
| `/help/<category>/` | Help topic | Article list | 404 if unpublished |
| `/help/<category>/<slug>/` | Help article | Article + coach CTA | 404 if unpublished |
| `/contact/` | Contact | Message sent + flash | Validation |
| `/about/` | Legal | About us | Unavailable copy |
| `/privacy/` | Legal | Privacy policy | Unavailable copy |
| `/terms/` | Legal | Terms of service | Unavailable copy |
| `/refund/` | Legal | Refund policy | Unavailable copy |
| `/disclaimer/` | Legal | Disclaimer | Unavailable copy |
| `/newsletter/` | Marketing | Subscribe (POST) | Invalid email |
| `/checkout/` | Purchase | Checkout form | Validation / payment |
| `/signup/` | Auth | Account created → session | Validation / email taken |
| `/login/` | Auth | Session → `/dashboard/` | Bad credentials |
| `/forgot/` | Auth | Reset email sent | Unknown email (soft) |
| `/logout/` | Auth | Session cleared → `/` | — |
| `/oauth/<provider>/` | Social auth | Redirect to provider | Unknown provider |
| `/password/change/` | Auth | Password updated | Validation / login required |
| `/onboarding/` | Onboarding 1–4 | Profile fields saved each step | Form validation; incomplete merchants cannot enter dashboard |
| `/onboarding/?step=2` | Onboarding step 2 | Business / niche / revenue | Cannot skip past saved `onboarding_step` (merchants) |
| `/onboarding/?step=3` | Onboarding step 3 | Goals / experience / success | Same |
| `/onboarding/?step=4` | Onboarding step 4 | Resources → `onboarding_completed=True` → `/dashboard/` | Challenges required; then enter dashboard |
| `/dashboard/` | Overview | Stats + coach entry | Redirect `/onboarding/` if not completed (non-staff) |
| `/dashboard/connect/` | Connect | Pending `ShopConnection` | Invalid domain / owned by other user |
| `/dashboard/create-store/` | Create store | Guide to open Shopify | — |
| `/dashboard/install/` | OAuth handoff | Redirect to Node | Missing shop / Node URL |
| `/dashboard/connect/error/` | OAuth fail | Retry message | Cancel / OAuth error |
| `/dashboard/builder/` | Builder wizard | Niche selected | No connected shop (customers) |
| `/dashboard/builder/start/` | Start build | Creates job → building | No shop / validation |
| `/dashboard/builder/building/<id>/` | Build running | Progress poll | Failed → retry / support |
| `/dashboard/builder/building/<id>/status/` | Build poll | JSON progress | Not found / forbidden |
| `/dashboard/builder/building/<id>/retry/` | Build retry | Restarts failed job | Not failed / forbidden |
| `/dashboard/builder/success/<id>/` | Build done | Store ready links | — |
| `/dashboard/builder/status/` | Builder API | JSON status | Login required |
| `/dashboard/product-hunter/` | Vault browse | Product cards (`?picks=1` AI Picks) | Empty vault / filters |
| `/dashboard/product-finder/` | Legacy | Redirects to Product Hunter | — |
| `/dashboard/winning-products/` | Legacy | Redirects to Product Hunter | — |
| `/dashboard/imports/` | My Imports | Drafts + push | No shop / Node publish error |
| `/dashboard/stores/` | My Stores | Rows + retry / open | Disconnect confirm |
| `/dashboard/stores/<id>/` | Store detail | Single store | Not found / forbidden |
| `/dashboard/stores/<id>/disconnect/` | Disconnect | Shop removed | Confirm / forbidden |
| `/dashboard/coach/` | Coach chat | AI chat + Help shortcuts (`?q=` prefill/send) | Login; live transfer needs Pro |
| `/dashboard/coach/api/session/` | Coach API | Poll messages | Login |
| `/dashboard/coach/api/send/` | Coach API | Send merchant message | Login |
| `/dashboard/coach/api/request-coach/` | Coach API | Request live coach | Pro plan / availability |
| `/dashboard/coach/api/close/` | Coach API | Close session | Login |
| `/dashboard/coach-desk/` | Coach desk | Staff inbox | Coach profile required |
| `/dashboard/schedule/` | Schedule | Live clock + book call | Slot taken / no open slots |
| `/dashboard/schedule/book/` | Book call | Slot reserved | Validation / taken |
| `/dashboard/training/` | Training | Lessons list | — |
| `/dashboard/settings/` | Settings | Account + prefs | — |
| `/dashboard/settings/profile/` | Edit profile | Same `MerchantProfile` fields | Validation / email taken |
| `/dashboard/upgrade/` | Upgrade | Plans / CTA | Billing not wired yet |
| `/api/address-suggest/?q=` | Address autocomplete | JSON suggestions | Login required |
| `/api/address-details/` | Place details | JSON address parts | Login required |
| `/api/geo/countries/?q=` | Country searchable dropdown | Worldwide country list | Login required |
| `/api/geo/states/?country_code=` | State/province dropdown | Subdivisions for selected country | Login required |
| `/api/geo/cities/` | City suggestions | City list for state | Login required |
| `/api/geo/timezone/` | Timezone resolve | Suggested timezone | Login required |
| `/api/geo/phone-meta/` | Phone dial meta | Dial code + example | Login required |
| `/admin/` | Staff admin | Full CRUD on all models | Not staff → login / 403 |
| `/404/` | Status preview (DEBUG) | Custom 404 template | Only when `DEBUG=True` |
| `/500/` | Status preview (DEBUG) | Custom 500 template | Only when `DEBUG=True` |
| `404` / `500` | Status (production) | Custom pages via handlers | `DEBUG=False`; `BBX-500-…` ref (500) |

**Onboarding gate:** any `/dashboard/*` request for a logged-in merchant with `MerchantProfile.onboarding_completed=False` redirects to `/onboarding/`. **Staff and superusers are not gated** — they can open any URL or wizard step for development/QA.

## Project tree

```text
BrandBoxWeb/
├── manage.py
├── requirements.txt
├── .env.example / .env.local          # secrets gitignored
├── config/
│   ├── settings.py                    # apps, DB, CATALOG_*, SHOPIFY_APP_URL
│   ├── urls.py                        # mounts apps + /admin/ + /help/
│   ├── product.py                     # OFFER_PERCENT, AFFILIATE_PERCENT, coach copy
│   ├── shopify.py                     # normalize shop + OAuth URL → Node
│   ├── brandbox_client.py             # all Node internal HTTP (secret header)
│   ├── middleware.py / context_processors.py
│   ├── celery.py                      # reserved for long builds
│   └── wsgi.py / asgi.py
├── apps/
│   ├── home/                          # landing /, affiliate, legal, contact
│   ├── accounts/                      # login, signup, logout, forgot
│   ├── help/                          # public Help Center (/help/)
│   │   ├── models.py                  # HelpCategory, HelpArticle, …
│   │   ├── seed_data.py / seed_help   # KB content
│   │   └── views.py / urls.py
│   ├── coach/                         # merchant chat API + coach desk
│   │   ├── models.py                  # CoachProfile, ChatSession, ChatMessage
│   │   ├── services.py / views.py
│   │   └── urls.py                    # /dashboard/coach/api/* + coach-desk/
│   ├── dashboard/                     # Overview, Connect, Vault, Imports, Stores, Coach page
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
│   │   └── urls.py                    # /dashboard/builder/* jobs
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
│   ├── accounts/  home/  checkout/  help/
│   ├── dashboard/                     # overview, connect, coach, finder, imports…
│   ├── builder/                       # building, success, failed
│   └── admin/catalog/scraperun/       # Start Hunting UI
├── static/
│   ├── css/                           # page CSS (home, affiliate, help, dashboard, …)
│   ├── js/                            # hero carousel, home scroll, product-finder, …
│   └── images/                        # niches, vault samples, logos
├── backups/                           # help_knowledge_base.json fixture
├── docs/                              # DEPLOY.md, …
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
  Hub --> Finder[Product Vault / Hunter]
  Hub --> Imports[My Imports]
  Hub --> Coach[BrandBox Coach]
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
  Eng --> Building[/dashboard/builder/building/id/]

  Sim --> Building
  Building --> Poll[Poll Node GET /api/build/status]
  Poll --> Sync[(DB UPDATE BuildJob<br/>progress / label / step)]
  Sync --> Done{Outcome?}

  Done -->|completed| Success[/dashboard/builder/success/id/<br/>BuildJob=done]
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

#### Overview / Finder / Push / Coach

```mermaid
flowchart TD
  Hub{Connected shop} --> OV[Overview]
  Hub --> BD[Builder — see chart above]
  Hub --> PF[Product Vault]
  Hub --> MI[My Imports]
  Hub --> CH[BrandBox Coach]

  OV --> OV1[(Read jobs + connection)]
  OV --> OV2[Node: product count]

  PF --> PF1[(Read CatalogProduct)]
  PF --> PF2{Import?}
  PF2 -->|Yes| PF3[(Write ShopImport)]

  MI --> MI1{Edit / Remove / Push}
  MI1 -->|Push| MI2[Node: create + publish]
  MI2 --> MI3[(ShopImport in_store)]

  CH --> CH1[AI reply from Help KB]
  CH --> CH2{Request live coach?}
  CH2 -->|Pro + available| CH3[Coach desk claim]
  CH2 -->|Free / offline| CH1
```

#### Help Center + Affiliate (public)

```mermaid
flowchart TD
  Home[/] --> Aff[/affiliate/]
  Home --> Help[/help/]
  Home --> CTA[Homepage CTAs]
  CTA --> Builder[/dashboard/builder/]
  CTA --> Vault[/dashboard/product-hunter/]
  CTA --> Coach[/dashboard/coach/]
  Help --> Topic[/help/category/]
  Topic --> Article[/help/category/slug/]
  Article --> AskCoach[Ask BrandBox Coach]
  AskCoach --> Coach
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
    HelpArticle
    ChatSession
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
| Help Center articles | Django | `HelpCategory`, `HelpArticle` |
| Coach chat | Django | `CoachProfile`, `ChatSession`, `ChatMessage` |
| Offer / affiliate display % | Django | `config/product.py` (not DB) |
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
3. /dashboard/builder/building/<id>/ polls:
     → Node GET /api/build/status
     → DB UPDATE BuildJob progress / status
4. Success → /dashboard/builder/success/<id>/   (BuildJob.status=done)
   Fail    → build_failed UI
   Retry   → Node POST /api/build/retry → new/linked job
```

**Staff preview shops:** may use a local timed simulator instead of Node.  
**Real shops:** theme/product upload runs in Node; webapp owns the guided UI + job rows.

---

### 5) Help Center + BrandBox Coach

```text
Public Help
  /help/  → search + browse HelpCategory / HelpArticle
  Seed: manage.py seed_help  OR  loaddata backups/help_knowledge_base.json

Merchant Coach
  /dashboard/coach/
    → get_or_create open ChatSession
    → AI replies from Help KB (apps/help)
    → ?q= from homepage chat prefill + auto-send
    → request live coach if UserPlan.is_pro

Coach desk (staff + CoachProfile.is_coach)
  /dashboard/coach-desk/
    → claim / reply / reassign / close sessions
```

---

### 6) Product Hunter → Winning Product Vault (admin / CLI)

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

**Merchant Product Hunter never reads the Sheet.** It reads `CatalogProduct` SQL only.

---

### 7) Product Hunter → Import draft

```text
1. /dashboard/product-hunter/
2. DB READ CatalogProduct via search_vault() (q / country / niche / page)
3. Import click → POST /dashboard/api/imports/
     → DB WRITE ShopImport (status=imported) for this shop+sourceId
     → cost/sell/compare from vault (USD); sell default = cost × 3
4. Badges: already imported / in_store from ShopImport rows for this shop

Node: not called for browse. Connect a real shop to Import (preview can browse only).
```

---

### 8) My Imports → edit → Push to Shopify

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

### 9) Node API map (Django → BrandBox)

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

### 10) Success & error summary

| Step | Success | Failure |
|------|---------|---------|
| Signup/Login | Session + `/dashboard/` (or `/onboarding/` if incomplete) | Form errors |
| Onboarding | Each step saved; step 4 → `onboarding_completed` + dashboard | Field validation; dashboard gated until done |
| Connect | Pending `ShopConnection` | Invalid domain / owned by other user |
| OAuth / install | `app_installed=True` | Connect error page; tunnel/secret wrong |
| Builder | `BuildJob` done + success page | Failed page + retry |
| Finder browse | Vault cards | Empty / connect banner for Import |
| Import | `ShopImport` created | Not in vault / no shop |
| Push | `in_store` + Shopify product | Toast: Node/tunnel/publish error |
| Coach chat | AI reply / live coach | Login; live transfer needs Pro |
| Help article | Published article | 404 if unpublished / missing seed |
| Affiliate register | Partner lead saved | Validation |
| Schedule book | `ScheduledCall` + next-call card | Slot taken / already booked |
| Server error | `BBX-500-…` page | Traceback only in logs |
| Superadmin | `/admin/` edit any profile / shop / job / Help / Coach | Must be `is_superuser` / staff |

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
python manage.py seed_help            # Help Center topics + articles
# or: python manage.py loaddata backups/help_knowledge_base.json
python manage.py createsuperuser   # for /admin/ (+ enable CoachProfile for desk)
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Useful public pages after seed:

- Help: [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/)
- Affiliate: [http://127.0.0.1:8000/affiliate/](http://127.0.0.1:8000/affiliate/)
- Coach (login): [http://127.0.0.1:8000/dashboard/coach/](http://127.0.0.1:8000/dashboard/coach/)

Change offer / affiliate % later in `config/product.py` (`OFFER_PERCENT`, `AFFILIATE_PERCENT`).

Set in `.env.local`:

```env
SHOPIFY_APP_URL=https://YOUR-TUNNEL.trycloudflare.com
BRANDBOX_INTERNAL_API_SECRET=brandbox-dev-shared-secret
CATALOG_SPREADSHEET_ID=...
CATALOG_SHEET_TAB=Meta Ads Products
GOOGLE_PLACES_API_KEY=your-browser-restricted-places-key
GEO_FALLBACK_COUNTRY=US
```

`GOOGLE_PLACES_API_KEY` powers Step 1 / Settings address autocomplete (Places API). Restrict the key by HTTP referrer in Google Cloud Console. Without it, Nominatim/Photon suggestions are used as a fallback.

Country pre-select uses IP geolocation (server + browser). On localhost the server cannot see your public IP, so the page refines Country in the browser via ipapi.co / ipinfo.io (and timezone as a last resort). Set `GEO_FALLBACK_COUNTRY=IN` (ISO2) if you want a different local default before that runs.

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
2. Wire billing / upgrade / one-time Pro pricing (after client finalizes numbers)
3. Celery worker for long Product Hunter / builds
4. Shared Postgres with BrandBox in staging/prod
5. Surface Node publish warnings (stock/scopes) clearly in My Imports toasts
6. Affiliate payouts / tracking beyond lead registration
