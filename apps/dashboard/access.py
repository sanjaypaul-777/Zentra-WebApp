"""Dev/staff access helpers — superuser & staff bypass product gates for QA."""


def is_dev_admin(user) -> bool:
    """True for staff/superuser — used to open any URL/step during development."""
    return bool(
        user is not None
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )
