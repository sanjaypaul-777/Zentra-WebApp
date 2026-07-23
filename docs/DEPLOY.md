# Deploy checklist

## Go live
1. Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL` (Postgres).
2. `python manage.py migrate`
3. Restore Help: `python manage.py loaddata backups/help_knowledge_base.json`  
   (or `python manage.py seed_help`)
4. Sync `media/` if you have Help uploads.
5. Enable **Coach** on staff users in Admin.
6. Test Coach, Coach desk, Help, Admin chat sessions.

## Change offer / affiliate % later
Edit only [`config/product.py`](../config/product.py):
- `OFFER_PERCENT = 65`
- `AFFILIATE_PERCENT = 30`

## Billing / upgrade / one-time price
Not wired yet — build after the client finalizes pricing.
