# Deploy checklist (BrandBoxWeb)

Ship **design + Django** first. Wire the **Node Shopify app** afterward with env vars — the site UI works without it (stores/builder/import push stay soft-disabled until linked).

## 1. Pre-flight (local)

```bash
python manage.py check
python manage.py check --deploy   # with DEBUG=False + real SECRET_KEY in env
python manage.py migrate --plan
```

Manual smoke (responsive + behavior):

- [ ] Home: hero → How → offer (2-col) → compare → Product Vault → FAQ
- [ ] Affiliate landing + register form (suggestions under fields)
- [ ] Login / signup / forgot (no empty black popup; suggestion under field)
- [ ] Dashboard mobile: hamburger opens/closes with proper `close` icon
- [ ] Help Center articles load after seed/loaddata

## 2. Production env (required now)

```env
SECRET_KEY=<long-random-50+chars>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/brandbox

MARKETING_URL=https://yourdomain.com
DASHBOARD_URL=https://yourdomain.com/dashboard/

# Email (contact / affiliate notify)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# …your SMTP settings…
DEFAULT_FROM_EMAIL=help@brandbox.co
CONTACT_NOTIFY_EMAIL=help@brandbox.co
```

Optional now:

```env
GOOGLE_PLACES_API_KEY=...
GEO_FALLBACK_COUNTRY=US
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

When `DEBUG=False`, Django enables SSL cookies / HSTS / redirect automatically (see `config/settings.py`). Behind a reverse proxy that already terminates TLS, you can set `SECURE_SSL_REDIRECT=False` if needed.

## 3. Go live commands

```bash
pip install -r requirements.txt
# Optional: rebuild homepage Tailwind CSS if you changed utility classes on home
# npm ci && npm run build:css
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py loaddata backups/help_knowledge_base.json
# or: python manage.py seed_help
python manage.py createsuperuser
```

Sync `media/` if you have Help uploads. Enable **Coach** on staff users in Admin.

**Static files:** With `DEBUG=False`, WhiteNoise serves `staticfiles/` (compressed + hashed). You do **not** need nginx to serve `/static/` unless you prefer it. Still serve `media/` from disk/object storage (uploads).

**Speed tip (optional CDN):** Put Cloudflare (or similar) in front of the app and enable caching + image polish/WebP. No app code change required — keeps layout/colors identical while shrinking image bytes on the wire.

## 4. After deploy — confirm design, then link Node

Leave these **empty** on first ship so marketing, auth, Help, and dashboard chrome are reviewable without Shopify:

```env
SHOPIFY_APP_URL=
BRANDBOX_INTERNAL_API_SECRET=
```

After you confirm the live design/experience, set both (same secret on Node) and restart:

```env
SHOPIFY_APP_URL=https://your-node-app.example
BRANDBOX_INTERNAL_API_SECRET=<shared-secret>
```

That unlocks install-status, AI Store Builder builds, and Product Vault → Shopify push. Spec for the Node side: [`docs/NODE_APP_PROMPT.md`](NODE_APP_PROMPT.md).

Affiliate **landing + register form** are design/lead-capture only until you add payouts/tracking later — no Node env required for the public pages.

## 5. Change offer / affiliate % later

Edit only [`config/product.py`](../config/product.py):

- `OFFER_PERCENT = 65`
- `AFFILIATE_PERCENT = 30`

## 6. Still not wired (OK for this deploy)

- Social OAuth / password-reset email
- Real card checkout / billing
- Affiliate commission payouts beyond lead registration
- Node Shopify link (section 4 — after design confirmation)
