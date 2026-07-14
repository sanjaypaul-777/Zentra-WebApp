# Zentra-Web workflow charts

Two separate accounts:

1. **Zentra login** = this webapp (`User`)
2. **Shopify store** = merchant’s `*.myshopify.com` (connected via Node OAuth)

---

## Full system (clear store states)

```mermaid
flowchart TD
  Start([Open Zentra Web]) --> Auth{Zentra logged in?}

  Auth -->|No| Login[Signup / Login]
  Login -->|Fail| Login
  Login -->|OK| Dash[/dashboard/]
  Auth -->|Yes| Dash

  Dash --> State{Shopify ↔ Zentra status}

  %% ——— Case A: no Shopify store yet ———
  State -->|No Shopify account yet| CreateCard[Create Shopify Account]
  CreateCard --> Partner[Shopify signup / free trial]
  Partner --> Back[Come back with *.myshopify.com]
  Back --> ConnectCard

  %% ——— Case B: has Shopify, not linked ———
  State -->|Has Shopify store<br/>but NOT connected| ConnectCard[Connect Shopify]
  ConnectCard --> Paste[Paste yourstorename.myshopify.com]
  Paste --> Pending[(DB: ShopConnection<br/>PENDING app_installed=false)]
  Pending --> InstallUI[Install Zentra guide]

  %% ——— Case C: domain saved, app not installed ———
  State -->|Domain saved<br/>pending install| InstallUI
  InstallUI --> OAuth[Redirect → Node OAuth]
  OAuth --> NodeSession[(Node: Shopify Session)]
  NodeSession --> Check[GET /api/install-status]
  Check -->|Not installed| InstallUI
  Check -->|Installed| Active[(DB: ShopConnection<br/>ACTIVE app_installed=true)]
  Active --> Dash

  %% ——— Case D: fully connected ———
  State -->|Already connected<br/>app_installed=true| Hub{Choose work}

  Hub --> Overview[Overview]
  Hub --> Builder[AI Store Builder]
  Hub --> Finder[Product Finder]
  Hub --> Imports[My Imports]
```

---

## Store status meanings

```mermaid
flowchart LR
  A[No Shopify store] --> B[Has Shopify store]
  B --> C[Pending in Zentra<br/>domain saved only]
  C --> D[Active in Zentra<br/>OAuth + app installed]

  A -.->|Create account| B
  B -.->|Connect + paste domain| C
  C -.->|Install / OAuth| D
```

| Status | Meaning | What user does |
|--------|---------|----------------|
| **No Shopify store** | Never created a Shopify shop | **Create Shopify Account** |
| **Has store, not connected** | Shop exists, Zentra doesn’t know it | **Connect** → paste `*.myshopify.com` |
| **Pending** | Domain in DB, `app_installed=false` | **Install Zentra** (Node OAuth) |
| **Active / connected** | `app_installed=true` | Overview, Builder, Finder Import, Push |

---

## AI Store Builder (full flow)

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

---

## Overview / Finder / Push

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

---

## Product Hunter → vault (staff)

```mermaid
flowchart TD
  H[Admin hunt] --> L{404?}
  L -->|Yes| S([Skip])
  L -->|No| U[USD prices]
  U --> V[(CatalogProduct)]
  U --> G[Sheet]
```

---

## Who owns what

```mermaid
flowchart LR
  subgraph ZentraWeb[Django webapp]
    User
    ShopConnection
    CatalogProduct
    ShopImport
    BuildJob
  end

  subgraph ZentraNode[Node app]
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
