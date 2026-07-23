"""
Simple display numbers — change these later when billing is final.

One-time payment / Pro pricing / upgrade rules will be built after deploy.
Do not put billing logic here yet.
"""

# Homepage Shopify offer badge number only (e.g. 65 → "65% Off")
OFFER_PERCENT = 65

# Affiliate page commission number only (e.g. 30 → "30%+")
AFFILIATE_PERCENT = 30

# Coach chat copy
COACH_WELCOME = "Hey — what do you want to get done today?"
COACH_STATUS_BOT = "You've got this — ask anything and grow with confidence."
COACH_STATUS_WAITING = "A coach is on the way — hang tight."
COACH_STATUS_CLOSED = "Chat closed — start a new message anytime."


def as_template_context() -> dict:
    return {
        "offer_badge": f"{OFFER_PERCENT}% Off",
        "offer_cta_lock_in": f"Lock in {OFFER_PERCENT}% off",
        "offer_cta_claim": f"Claim {OFFER_PERCENT}% Discount",
        "offer_footnote": (
            f"*{OFFER_PERCENT}% off Plus annual for year one. "
            "Renews at the standard rate unless canceled. Offer may change."
        ),
        "offer_faq_blurb": (
            f"Eligible customers can get {OFFER_PERCENT}% off Plus Annual for the first year. "
            "Check checkout for the current price and what’s included on your plan."
        ),
        "affiliate_commission_label": f"{AFFILIATE_PERCENT}%+",
        "affiliate_commission_blurb": (
            f"{AFFILIATE_PERCENT}%+ on every referred sale, not a flat one-time fee."
        ),
        "affiliate_commission_detail": (
            f"Partners start at {AFFILIATE_PERCENT}%+ commission per sale, with rates that "
            "can increase based on performance."
        ),
    }
