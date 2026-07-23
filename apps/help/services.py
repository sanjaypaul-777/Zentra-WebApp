from __future__ import annotations

import re
from collections.abc import Iterable

from django.db.models import Q

from .models import HelpArticle

# US ↔ UK spelling
_SPELLING_VARIANTS: dict[str, tuple[str, ...]] = {
    "fulfilment": ("fulfillment", "fulfilment"),
    "fulfillment": ("fulfillment", "fulfilment"),
    "fulfil": ("fulfill", "fulfil"),
    "fulfill": ("fulfill", "fulfil"),
    "fulfils": ("fulfills", "fulfils"),
    "fulfills": ("fulfills", "fulfils"),
    "cancelled": ("canceled", "cancelled"),
    "canceled": ("canceled", "cancelled"),
    "colour": ("color", "colour"),
    "color": ("color", "colour"),
    "centre": ("center", "centre"),
    "center": ("center", "centre"),
    "licence": ("license", "licence"),
    "license": ("license", "licence"),
}

# Word → related search terms (intent expansion)
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "order": ("order", "orders", "fulfillment", "fulfilment", "shipping", "tracking", "wismo"),
    "orders": ("order", "orders", "fulfillment", "fulfilment", "shipping"),
    "fulfilment": ("fulfillment", "fulfilment", "shipping", "supplier", "dropshipping", "order"),
    "fulfillment": ("fulfillment", "fulfilment", "shipping", "supplier", "dropshipping", "order"),
    "fulfil": ("fulfill", "fulfil", "fulfillment", "shipping"),
    "ship": ("shipping", "ship", "delivery", "tracking", "fulfillment"),
    "shipping": ("shipping", "delivery", "tracking", "rates", "zones", "fulfillment", "customs"),
    "delivery": ("delivery", "shipping", "tracking", "arrived"),
    "track": ("tracking", "track", "tracking number", "shipment"),
    "tracking": ("tracking", "tracking number", "shipment", "carrier", "where"),
    "wismo": ("where", "order", "tracking", "shipping"),
    "where": ("where", "tracking", "order", "shipping", "arrived"),
    "refund": ("refund", "refunds", "return", "chargeback", "money back"),
    "refunds": ("refund", "return", "chargeback"),
    "return": ("return", "returns", "refund", "policy"),
    "returns": ("return", "returns", "refund", "policy"),
    "chargeback": ("chargeback", "dispute", "refund", "evidence"),
    "dispute": ("dispute", "chargeback", "claim"),
    "cancel": ("cancel", "cancellation", "refund"),
    "cancellation": ("cancellation", "cancel", "before fulfillment"),
    "stock": ("stock", "out of stock", "inventory", "supplier", "restock"),
    "oos": ("out of stock", "inventory", "supplier"),
    "supplier": ("supplier", "suppliers", "dropship", "fulfillment", "sku"),
    "suppliers": ("supplier", "dropship", "fulfillment"),
    "dropship": ("dropshipping", "dropship", "supplier", "fulfillment"),
    "dropshipping": ("dropshipping", "supplier", "fulfillment", "shipping"),
    "payment": ("payment", "payments", "gateway", "payout", "shopify payments"),
    "payments": ("payment", "gateway", "payout", "tax"),
    "tax": ("tax", "taxes", "sales tax", "duties", "vat"),
    "taxes": ("tax", "sales tax", "duties"),
    "ad": ("ads", "advertising", "facebook", "instagram", "tiktok", "budget"),
    "ads": ("ads", "facebook", "instagram", "tiktok", "marketing", "traffic"),
    "facebook": ("facebook", "instagram", "meta", "ads"),
    "instagram": ("instagram", "facebook", "meta", "ads"),
    "tiktok": ("tiktok", "ads", "marketing"),
    "seo": ("seo", "search", "meta", "sitemap"),
    "email": ("email", "abandoned cart", "klaviyo", "newsletter"),
    "cart": ("abandoned cart", "checkout", "email"),
    "analytics": ("analytics", "conversion", "cac", "growth", "shopify analytics"),
    "conversion": ("conversion", "conversion rate", "analytics"),
    "cac": ("customer acquisition cost", "cac", "ads", "budget"),
    "scale": ("scale", "ad spend", "growth", "budget"),
    "niche": ("niche", "builder", "theme", "ai store builder"),
    "builder": ("ai store builder", "niche", "build", "theme"),
    "build": ("build", "builder", "ai store", "failed"),
    "import": ("import", "imports", "product hunter", "push"),
    "imports": ("imports", "my imports", "push", "product"),
    "push": ("push", "publish", "shopify", "imports"),
    "hunter": ("product hunter", "winning", "vault", "ai picks"),
    "product": ("product", "products", "hunter", "imports", "listing"),
    "shopify": ("shopify", "store", "connect", "theme", "app"),
    "store": ("store", "shopify", "my stores", "connect"),
    "coach": ("coach", "chat", "support", "help", "ai"),
    "support": ("support", "customer service", "coach", "contact", "refund"),
    "customer": ("customer", "support", "refund", "service", "angry"),
    "angry": ("angry", "difficult", "customer service"),
    "policy": ("policy", "policies", "privacy", "terms", "refund"),
    "privacy": ("privacy", "gdpr", "policy"),
    "gdpr": ("gdpr", "privacy", "eu", "deletion"),
    "affiliate": ("affiliate", "commission", "referral", "apply"),
    "password": ("password", "login", "account"),
    "login": ("login", "password", "account", "cant log"),
    "billing": ("billing", "pro", "upgrade", "payment", "plan"),
    "pro": ("pro", "upgrade", "plan", "billing"),
    "upgrade": ("upgrade", "pro", "plan"),
    "customs": ("customs", "duties", "international", "import"),
    "duties": ("duties", "customs", "international"),
    "insurance": ("insurance", "shipping insurance"),
    "gateway": ("gateway", "payments", "shopify payments"),
    "payout": ("payout", "payouts", "payments"),
    "currency": ("currency", "conversion", "international"),
    "influencer": ("influencer", "affiliate", "outreach"),
    "license": ("license", "licence", "business license"),
    "licence": ("license", "licence", "business license"),
    "qc": ("quality control", "bad batches", "supplier"),
    "quality": ("quality control", "bad batches", "supplier"),
    "sku": ("sku", "mapping", "supplier", "listing", "link"),
    "listing": ("listing", "listings", "product", "out of stock", "link"),
    "link": ("link", "linking", "map", "mapping", "supplier", "product", "fulfillment"),
    "linking": ("link", "linking", "map", "supplier", "product"),
    "map": ("map", "mapping", "link", "sku", "supplier"),
    "mapping": ("mapping", "map", "link", "sku", "supplier"),
    "connect": ("connect", "shopify", "install", "store", "link", "supplier"),
    "automation": ("automating", "automation", "fulfillment", "supplier", "tracking"),
    "automate": ("automating", "automation", "fulfillment", "link"),
    "existing": ("existing", "link", "supplier", "products", "store"),
}

# Phrase intents → boost keywords (matched against title/summary/category)
_PHRASE_INTENTS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"where.?s?\s+my\s+order|wismo|order\s+status", re.I), ("where", "order", "tracking")),
    (re.compile(r"out\s+of\s+stock|oos|no\s+stock", re.I), ("out of stock", "supplier", "inventory")),
    (re.compile(r"wrong\s+item|incorrect\s+item|wrong\s+product", re.I), ("wrong item", "supplier")),
    (re.compile(r"never\s+arrived|didn.?t\s+arrive|not\s+received", re.I), ("never arrived", "tracking")),
    (re.compile(r"not\s+as\s+described|not\s+like\s+photo", re.I), ("not as described",)),
    (re.compile(r"charge\s*back|bank\s+dispute", re.I), ("chargeback", "dispute")),
    (re.compile(r"free\s+shipping|flat\s+rate|shipping\s+rate", re.I), ("shipping", "rates")),
    (re.compile(r"sales\s+tax|vat|charge\s+tax", re.I), ("tax", "sales tax")),
    (re.compile(r"connect\s+(my\s+)?store|install\s+app", re.I), ("connect", "shopify", "install")),
    (re.compile(r"ai\s+store|store\s+builder|choose\s+niche", re.I), ("ai store builder", "niche")),
    (re.compile(r"winning\s+score|product\s+hunter|ai\s+picks", re.I), ("product hunter", "winning")),
    (re.compile(r"push\s+to\s+shopify|publish\s+product", re.I), ("push", "imports")),
    (re.compile(r"talk\s+to\s+(a\s+)?coach|human\s+support|live\s+chat", re.I), ("coach", "support")),
    (re.compile(r"can.?t\s+log\s*in|forgot\s+password", re.I), ("login", "password")),
    (re.compile(r"facebook\s+ad|instagram\s+ad|meta\s+ad", re.I), ("facebook", "instagram", "ads")),
    (re.compile(r"tik\s*tok", re.I), ("tiktok", "ads")),
    (re.compile(r"abandoned\s+cart", re.I), ("abandoned cart", "email")),
    (re.compile(r"business\s+license|need\s+a\s+license", re.I), ("business license",)),
    (re.compile(r"partial\s+ship|split\s+shipment|multi.?supplier", re.I), ("partial", "suppliers")),
    (re.compile(r"switch(ing)?\s+supplier", re.I), ("switching suppliers", "supplier")),
    (
        re.compile(
            r"link(ing)?\s+(existing\s+)?product|connect\s+product\s+to\s+supplier|map\s+product|who\s+is\s+(the\s+)?supplier|product\s+to\s+supplier",
            re.I,
        ),
        ("link", "existing", "supplier", "product", "mapping", "fulfillment"),
    ),
)

_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "for",
        "of",
        "and",
        "or",
        "in",
        "on",
        "my",
        "me",
        "i",
        "is",
        "are",
        "how",
        "what",
        "when",
        "do",
        "does",
        "can",
        "with",
        "from",
        "about",
        "please",
        "help",
        "need",
        "want",
        "get",
        "got",
    }
)


def _token_variants(token: str) -> list[str]:
    key = token.lower().strip()
    if not key:
        return []
    out: list[str] = [key]
    out.extend(_SPELLING_VARIANTS.get(key, ()))
    out.extend(_SYNONYMS.get(key, ()))
    # Light stemming
    if key.endswith("ing") and len(key) > 5:
        out.append(key[:-3])
        out.append(key[:-3] + "e")
    if key.endswith("ed") and len(key) > 4:
        out.append(key[:-2])
    if key.endswith("s") and len(key) > 3 and not key.endswith("ss"):
        out.append(key[:-1])
    return list(dict.fromkeys(v for v in out if v and v not in _STOP))


def _expand_query(q: str) -> list[str]:
    raw = (q or "").strip().lower()
    if not raw:
        return []
    terms: list[str] = []
    for pattern, boosts in _PHRASE_INTENTS:
        if pattern.search(raw):
            terms.extend(boosts)
    for token in re.findall(r"[a-z0-9']+", raw):
        if token in _STOP or len(token) < 2:
            continue
        terms.extend(_token_variants(token))
    # Keep order, unique
    return list(dict.fromkeys(terms))


def _blob(article: HelpArticle) -> str:
    return " ".join(
        [
            article.title or "",
            article.summary or "",
            article.category.name if article.category_id else "",
            article.slug or "",
            article.body or "",
        ]
    ).lower()


def _score_article(article: HelpArticle, terms: Iterable[str], raw_q: str) -> float:
    title = (article.title or "").lower()
    summary = (article.summary or "").lower()
    category = (article.category.name if article.category_id else "").lower()
    slug = (article.slug or "").lower()
    body = (article.body or "").lower()
    blob = _blob(article)
    raw = raw_q.lower().strip()
    score = 0.0

    if raw and raw in title:
        score += 120
    elif raw and raw in summary:
        score += 70
    elif raw and raw in blob:
        score += 25

    seen = set()
    for term in terms:
        t = term.lower()
        if not t or t in seen:
            continue
        seen.add(t)
        if t in title:
            score += 40
        elif t in summary:
            score += 22
        elif t in category or t in slug:
            score += 18
        elif t in body:
            score += 8
        # Partial word (e.g. fulfil inside fulfillment)
        elif len(t) >= 4 and any(t in w for w in title.split()):
            score += 28

    # Prefer non-coming-soon slightly when scores tie-ish
    if article.is_coming_soon:
        score -= 5
    return score


def search_articles(q: str, limit: int | None = 40) -> list[HelpArticle]:
    """Intent-aware Help search: synonyms, phrase intents, ranked relevance."""
    raw = (q or "").strip()
    if not raw:
        return []

    terms = _expand_query(raw)
    if not terms:
        terms = [t for t in re.findall(r"[a-z0-9']+", raw.lower()) if t not in _STOP]

    # Broad candidate pull: any expanded term hits (OR), then rank in Python
    candidate_q = Q()
    for term in terms[:40]:
        candidate_q |= (
            Q(title__icontains=term)
            | Q(summary__icontains=term)
            | Q(body__icontains=term)
            | Q(category__name__icontains=term)
            | Q(slug__icontains=term)
        )

    # Also match original tokens tightly
    for token in re.findall(r"[a-z0-9']+", raw.lower()):
        if token in _STOP:
            continue
        for variant in _token_variants(token):
            candidate_q |= (
                Q(title__icontains=variant)
                | Q(summary__icontains=variant)
                | Q(body__icontains=variant)
                | Q(category__name__icontains=variant)
            )

    qs = (
        HelpArticle.objects.filter(
            is_published=True,
            category__is_published=True,
        )
        .filter(candidate_q)
        .select_related("category")
        .distinct()[:200]
    )

    scored = []
    for article in qs:
        s = _score_article(article, terms, raw)
        if s > 0:
            scored.append((s, article.pk, article))

    scored.sort(key=lambda row: (-row[0], row[1]))
    articles = [a for _, _, a in scored]
    if limit is not None:
        return articles[:limit]
    return articles


def suggest_articles_for_query(q: str, limit: int = 3) -> list[HelpArticle]:
    return search_articles(q, limit=limit)
