"""
IP → country detection + worldwide country/state lists (pycountry).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any

import pycountry
from django.conf import settings

_UA = "BrandBoxWeb/1.0 (geo; help@brandbox.co)"


def client_ip(request) -> str:
    """Best-effort client IP (supports common reverse-proxy headers)."""
    for header in (
        "HTTP_CF_CONNECTING_IP",
        "HTTP_TRUE_CLIENT_IP",
        "HTTP_X_REAL_IP",
    ):
        val = (request.META.get(header) or "").strip()
        if val:
            return val.split(",")[0].strip()
    xff = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if xff:
        return xff.split(",")[0].strip()
    return (request.META.get("REMOTE_ADDR") or "").strip()


def _is_loopback(ip: str) -> bool:
    ip = (ip or "").strip().lower()
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return True
    if ip.startswith("127."):
        return True
    return False


def country_name_for_code(code: str) -> str:
    code = (code or "").upper()
    if not code:
        return ""
    try:
        c = pycountry.countries.get(alpha_2=code)
        if c is not None:
            return c.name
    except (KeyError, AttributeError, TypeError):
        pass
    return code


def country_code_for_name(name: str) -> str:
    """Best-effort ISO2 for a country display name."""
    name = (name or "").strip()
    if not name:
        return ""
    if len(name) == 2 and name.isalpha():
        return name.upper()
    try:
        matches = pycountry.countries.search_fuzzy(name)
        if matches:
            return matches[0].alpha_2
    except LookupError:
        pass
    # Exact / casefold scan
    target = name.casefold()
    for c in pycountry.countries:
        if c.name.casefold() == target:
            return c.alpha_2
        official = getattr(c, "official_name", None)
        if official and str(official).casefold() == target:
            return c.alpha_2
    return ""


def detect_country(request) -> dict[str, str]:
    """
    Return {"code", "name", "confident", "source"} from IP / CDN headers.

    confident=False when we only have GEO_FALLBACK (e.g. localhost) — the
    browser should refine via client-side IP geolocation.
    """
    # Cloudflare / similar edge country (usually accurate)
    cf = (request.META.get("HTTP_CF_IPCOUNTRY") or "").strip().upper()
    if cf and cf not in ("XX", "T1"):
        return {
            "code": cf,
            "name": country_name_for_code(cf),
            "confident": True,
            "source": "cdn",
        }

    ip = client_ip(request)
    session = getattr(request, "session", None)

    # Loopback / private → cannot geolocate from the server; mark low confidence
    if _is_loopback(ip) or _is_private_ip(ip):
        fallback = (getattr(settings, "GEO_FALLBACK_COUNTRY", None) or "US").upper()
        return {
            "code": fallback,
            "name": country_name_for_code(fallback),
            "confident": False,
            "source": "fallback",
        }

    if session is not None:
        cached = session.get("geo_country")
        if (
            isinstance(cached, dict)
            and cached.get("code")
            and cached.get("ip") == ip
            and cached.get("confident") is True
        ):
            return {
                "code": str(cached["code"]).upper(),
                "name": cached.get("name") or country_name_for_code(cached["code"]),
                "confident": True,
                "source": cached.get("source") or "cache",
            }

    looked = _lookup_ip_country(ip)
    if session is not None and looked.get("code") and looked.get("confident"):
        session["geo_country"] = {**looked, "ip": ip}
    return looked


def _is_private_ip(ip: str) -> bool:
    ip = (ip or "").strip()
    if not ip:
        return True
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("169.254."):
        return True
    # 172.16.0.0 – 172.31.255.255
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
            if 16 <= second <= 31:
                return True
        except (IndexError, ValueError):
            pass
    return False


def _lookup_ip_country(ip: str) -> dict[str, str]:
    """Try several free IP→country providers; fall back with confident=False."""
    fallback = (getattr(settings, "GEO_FALLBACK_COUNTRY", None) or "US").upper()
    for provider in (_lookup_ipapi, _lookup_ipinfo, _lookup_ip_api):
        try:
            result = provider(ip)
        except Exception:
            result = None
        if result and result.get("code"):
            result["confident"] = True
            return result
    return {
        "code": fallback,
        "name": country_name_for_code(fallback),
        "confident": False,
        "source": "fallback",
    }


def _http_get_json(url: str, *, timeout: float = 3) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": _UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _lookup_ipapi(ip: str) -> dict[str, str] | None:
    data = _http_get_json(f"https://ipapi.co/{urllib.parse.quote(ip)}/json/")
    if data.get("error"):
        return None
    code = (data.get("country_code") or "").strip().upper()
    if not code:
        return None
    name = (data.get("country_name") or "").strip()
    return {
        "code": code,
        "name": name or country_name_for_code(code),
        "source": "ipapi",
    }


def _lookup_ipinfo(ip: str) -> dict[str, str] | None:
    # Free tier without token is fine for low volume
    data = _http_get_json(f"https://ipinfo.io/{urllib.parse.quote(ip)}/json")
    code = (data.get("country") or "").strip().upper()
    if not code or len(code) != 2:
        return None
    return {
        "code": code,
        "name": country_name_for_code(code),
        "source": "ipinfo",
    }


def _lookup_ip_api(ip: str) -> dict[str, str] | None:
    # ip-api.com — HTTP only on free tier
    data = _http_get_json(
        f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields=status,country,countryCode"
    )
    if data.get("status") != "success":
        return None
    code = (data.get("countryCode") or "").strip().upper()
    if not code:
        return None
    name = (data.get("country") or "").strip()
    return {
        "code": code,
        "name": name or country_name_for_code(code),
        "source": "ip-api",
    }


# Common IANA timezones → ISO2 (used as client-side hint when IP APIs fail)
TIMEZONE_COUNTRY: dict[str, str] = {
    "Asia/Kolkata": "IN",
    "Asia/Calcutta": "IN",
    "America/New_York": "US",
    "America/Chicago": "US",
    "America/Denver": "US",
    "America/Los_Angeles": "US",
    "America/Toronto": "CA",
    "America/Vancouver": "CA",
    "Europe/London": "GB",
    "Europe/Paris": "FR",
    "Europe/Berlin": "DE",
    "Europe/Amsterdam": "NL",
    "Europe/Madrid": "ES",
    "Europe/Rome": "IT",
    "Australia/Sydney": "AU",
    "Australia/Melbourne": "AU",
    "Pacific/Auckland": "NZ",
    "Asia/Dubai": "AE",
    "Asia/Singapore": "SG",
    "Asia/Tokyo": "JP",
    "Asia/Shanghai": "CN",
    "Asia/Hong_Kong": "HK",
    "Asia/Manila": "PH",
    "Asia/Karachi": "PK",
    "Asia/Dhaka": "BD",
    "Africa/Lagos": "NG",
    "Africa/Johannesburg": "ZA",
    "America/Sao_Paulo": "BR",
    "America/Mexico_City": "MX",
    "Europe/Dublin": "IE",
}


def country_from_timezone(tz_name: str) -> dict[str, str] | None:
    code = TIMEZONE_COUNTRY.get((tz_name or "").strip())
    if not code:
        # Soft match: Asia/Kolkata-style already covered; try region prefix heuristics
        return None
    return {"code": code, "name": country_name_for_code(code), "source": "timezone"}


def resolve_initial_country(
    *,
    profile_country: str = "",
    geo: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Prefer a saved profile country; otherwise IP-detected geo.
    """
    saved = (profile_country or "").strip()
    if saved:
        code = country_code_for_name(saved)
        if code:
            return {
                "code": code,
                "name": country_name_for_code(code) or saved,
                "confident": True,
                "source": "profile",
            }
        return {"code": "", "name": saved, "confident": True, "source": "profile"}
    if geo and geo.get("code"):
        return {
            "code": str(geo["code"]).upper(),
            "name": geo.get("name") or country_name_for_code(geo["code"]),
            "confident": bool(geo.get("confident", True)),
            "source": geo.get("source") or "geo",
        }
    return {
        "code": "US",
        "name": country_name_for_code("US"),
        "confident": False,
        "source": "fallback",
    }

@lru_cache(maxsize=1)
def all_countries() -> tuple[dict[str, str], ...]:
    rows = [
        {"code": c.alpha_2, "name": c.name}
        for c in pycountry.countries
        if getattr(c, "alpha_2", None)
    ]
    rows.sort(key=lambda r: r["name"].casefold())
    return tuple(rows)


def filter_countries(q: str, *, limit: int = 300) -> list[dict[str, str]]:
    """Filter worldwide countries. Empty q returns the full list (up to limit)."""
    q = (q or "").strip().casefold()
    rows = list(all_countries())
    if not q:
        return rows[:limit]
    starts = [
        r
        for r in rows
        if r["name"].casefold().startswith(q) or r["code"].casefold() == q
    ]
    contains = [r for r in rows if q in r["name"].casefold() and r not in starts]
    return (starts + contains)[:limit]


def google_place_autocomplete(
    q: str, *, country_code: str = "", limit: int = 8
) -> list[dict[str, str]]:
    """Google Places Autocomplete (HTTP). Returns [{label, place_id}, ...]."""
    key = (getattr(settings, "GOOGLE_PLACES_API_KEY", None) or "").strip()
    if not key or len(q) < 2:
        return []
    params: dict[str, str] = {
        "input": q,
        "key": key,
        "language": "en",
    }
    # Broader than types=address — partial street names match better
    if country_code:
        params["components"] = f"country:{country_code.strip().lower()}"
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json?" + urllib.parse.urlencode(
        params
    )
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return []
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return []
    out: list[dict[str, str]] = []
    for pred in data.get("predictions") or []:
        label = (pred.get("description") or "").strip()
        place_id = (pred.get("place_id") or "").strip()
        if label and place_id:
            out.append({"label": label, "place_id": place_id})
        if len(out) >= limit:
            break
    return out


def google_place_details(place_id: str) -> dict[str, str] | None:
    """Resolve a place_id into street/city/state/zip/country fields."""
    key = (getattr(settings, "GOOGLE_PLACES_API_KEY", None) or "").strip()
    place_id = (place_id or "").strip()
    if not key or not place_id:
        return None
    params = {
        "place_id": place_id,
        "key": key,
        "fields": "address_component,formatted_address",
        "language": "en",
    }
    url = "https://maps.googleapis.com/maps/api/place/details/json?" + urllib.parse.urlencode(
        params
    )
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    if data.get("status") != "OK":
        return None
    result = data.get("result") or {}
    comps = result.get("address_components") or []
    by_type: dict[str, dict] = {}
    for c in comps:
        for t in c.get("types") or []:
            by_type[t] = c

    def long(t: str) -> str:
        row = by_type.get(t) or {}
        return (row.get("long_name") or "").strip()

    def short(t: str) -> str:
        row = by_type.get(t) or {}
        return (row.get("short_name") or "").strip()

    street = " ".join(p for p in (long("street_number"), long("route")) if p).strip()
    city = (
        long("locality")
        or long("postal_town")
        or long("sublocality_level_1")
        or long("administrative_area_level_2")
    )
    state = long("administrative_area_level_1")
    if state:
        state = match_state_name(short("country"), state) or state
    return {
        "street": street,
        "city": city,
        "state": state,
        "zip": long("postal_code"),
        "country": long("country"),
        "country_code": short("country").upper(),
        "label": (result.get("formatted_address") or "").strip(),
    }


def nominatim_address_suggest(
    q: str, *, country_code: str = "", country_name: str = "", limit: int = 8
) -> list[dict[str, str]]:
    """OpenStreetMap Nominatim fallback — bias query with country name."""
    code = (country_code or "").strip().upper()
    name = (country_name or country_name_for_code(code) or "").strip()
    query = q.strip()
    if name and name.casefold() not in query.casefold():
        query = f"{query}, {name}"
    params: dict[str, str | int] = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
    }
    if code:
        params["countrycodes"] = code.lower()
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": _UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "[]")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return []

    results: list[dict[str, str]] = []
    for row in payload if isinstance(payload, list) else []:
        addr = row.get("address") or {}
        street_parts = [
            addr.get("house_number") or "",
            addr.get("road") or addr.get("pedestrian") or addr.get("residential") or "",
        ]
        street = " ".join(p for p in street_parts if p).strip()
        if not street:
            street = (
                addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("hamlet")
                or ""
            ).strip()
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or addr.get("county")
            or ""
        ).strip()
        state = (addr.get("state") or addr.get("region") or "").strip()
        postcode = (addr.get("postcode") or "").strip()
        row_cc = (addr.get("country_code") or code or "").upper()
        row_country = country_name_for_code(row_cc) or (addr.get("country") or name)
        label = (row.get("display_name") or "").strip()
        if not label:
            continue
        if state and row_cc:
            state = match_state_name(row_cc, state) or state
        results.append(
            {
                "label": label,
                "street": street,
                "city": city,
                "state": state,
                "zip": postcode,
                "country": row_country,
                "country_code": row_cc,
            }
        )
    return results


def photon_address_suggest(
    q: str, *, country_code: str = "", limit: int = 8
) -> list[dict[str, str]]:
    """Komoot Photon geocoder — often stronger for partial street queries."""
    code = (country_code or "").strip().upper()
    params: dict[str, str | int] = {"q": q.strip(), "limit": limit, "lang": "en"}
    if code:
        # Photon uses ISO3 sometimes; also pass osm bbox via location_bias later if needed
        pass
    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return []

    results: list[dict[str, str]] = []
    for feat in data.get("features") or []:
        props = feat.get("properties") or {}
        feat_cc = (props.get("countrycode") or "").upper()
        if code and feat_cc and feat_cc != code:
            continue
        street_parts = [
            str(props.get("housenumber") or ""),
            str(props.get("street") or props.get("name") or ""),
        ]
        street = " ".join(p for p in street_parts if p).strip()
        city = (props.get("city") or props.get("town") or props.get("village") or "").strip()
        state = (props.get("state") or "").strip()
        postcode = str(props.get("postcode") or "").strip()
        country = (props.get("country") or country_name_for_code(feat_cc)).strip()
        # Build label
        bits = [b for b in (street, city, state, country) if b]
        label = ", ".join(bits) if bits else (props.get("name") or "").strip()
        if not label:
            continue
        if state and feat_cc:
            state = match_state_name(feat_cc, state) or state
        results.append(
            {
                "label": label,
                "street": street or (props.get("name") or "").strip(),
                "city": city,
                "state": state,
                "zip": postcode,
                "country": country,
                "country_code": feat_cc,
            }
        )
        if len(results) >= limit:
            break
    return results



@lru_cache(maxsize=128)
def states_for_country_code(country_code: str) -> tuple[str, ...]:
    """State/province names for an ISO2 country code (ISO 3166-2 via pycountry)."""
    code = (country_code or "").strip().upper()
    if not code:
        return ()
    try:
        subs = list(pycountry.subdivisions.get(country_code=code))
    except (KeyError, AttributeError, TypeError):
        return ()
    names = []
    for s in subs:
        n = _plain_place_name(getattr(s, "name", None) or "")
        if n:
            names.append(n)
    return tuple(sorted(set(names), key=str.casefold))


def _plain_place_name(name: str) -> str:
    """
    ISO subdivision data often includes macrons (Uttarākhand).
    Strip combining marks so UI matches everyday English spellings.
    """
    import unicodedata

    raw = (name or "").strip()
    if not raw:
        return ""
    decomposed = unicodedata.normalize("NFKD", raw)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).strip()


@lru_cache(maxsize=64)
def states_for_country(country_name_or_code: str) -> tuple[str, ...]:
    """Accept ISO2 or country name."""
    raw = (country_name_or_code or "").strip()
    if not raw:
        return ()
    if len(raw) == 2 and raw.isalpha():
        return states_for_country_code(raw.upper())
    code = country_code_for_name(raw)
    if code:
        return states_for_country_code(code)
    return ()


def _http_json(url: str, *, data: dict | None = None, timeout: float = 6) -> Any:
    body = None
    headers = {"User-Agent": _UA, "Accept": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


@lru_cache(maxsize=256)
def cities_for_state(country_name: str, state_name: str) -> tuple[str, ...]:
    """Optional city list (kept for Settings compatibility)."""
    country = (country_name or "").strip()
    state = (state_name or "").strip()
    if not country or not state:
        return ()
    try:
        payload = _http_json(
            "https://countriesnow.space/api/v0.1/countries/state/cities",
            data={"country": country, "state": state},
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return ()
    if not isinstance(payload, dict) or payload.get("error"):
        return ()
    data = payload.get("data") or []
    names = [str(c).strip() for c in data if str(c).strip()]
    return tuple(sorted(set(names), key=str.casefold))


def filter_names(names: tuple[str, ...] | list[str], q: str, *, limit: int = 40) -> list[str]:
    q = (q or "").strip().casefold()
    if not q:
        return list(names)[:limit]
    starts = [n for n in names if n.casefold().startswith(q)]
    contains = [n for n in names if q in n.casefold() and n not in starts]
    return (starts + contains)[:limit]


def match_state_name(country_code: str, candidate: str) -> str:
    """Map a Places/admin area string onto a known subdivision name when possible."""
    cand = (candidate or "").strip()
    if not cand:
        return ""
    states = states_for_country_code(country_code)
    if not states:
        return cand
    cf = cand.casefold()
    for s in states:
        if s.casefold() == cf:
            return s
    for s in states:
        if cf in s.casefold() or s.casefold() in cf:
            return s
    return cand


def phone_meta_for_country(country_code: str) -> dict[str, str]:
    """
    Dial code + example placeholder for a country (Google libphonenumber).
    """
    import phonenumbers
    from phonenumbers import PhoneNumberFormat, PhoneNumberType
    from phonenumbers.phonenumberutil import country_code_for_region

    code = (country_code or "").strip().upper() or "US"
    try:
        dial = country_code_for_region(code)
    except Exception:
        dial = 0
    dial_str = f"+{dial}" if dial else ""

    example = ""
    try:
        num = phonenumbers.example_number_for_type(
            code, PhoneNumberType.MOBILE
        ) or phonenumbers.example_number_for_type(
            code, PhoneNumberType.FIXED_LINE_OR_MOBILE
        )
        if num is not None:
            example = phonenumbers.format_number(num, PhoneNumberFormat.NATIONAL)
            # Strip leading trunk 0 from some national examples for placeholder clarity
            example = example.lstrip("0").strip() if example.startswith("0") else example
    except Exception:
        example = ""

    return {
        "country_code": code,
        "dial_code": dial_str,
        "example": example,
        "placeholder": f"{dial_str} {example}".strip() if example else dial_str or "Phone",
    }


def normalize_phone(raw: str, *, country_code: str = "") -> str:
    """
    Parse a phone number and return E.164 (+919876543210) when possible.
    Falls back to a cleaned original string if parsing fails.
    """
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat

    text = (raw or "").strip()
    if not text:
        return ""
    region = (country_code or "").strip().upper() or None
    try:
        parsed = phonenumbers.parse(text, region)
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        pass
    # Keep digits / leading +
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    return cleaned or text


def format_phone_display(raw: str, *, country_code: str = "") -> str:
    """International display format when parseable."""
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat

    text = (raw or "").strip()
    if not text:
        return ""
    region = (country_code or "").strip().upper() or None
    try:
        parsed = phonenumbers.parse(text, region)
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
    except NumberParseException:
        pass
    return text
