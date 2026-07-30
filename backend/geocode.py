import json
import re
import urllib.parse
import urllib.request

USER_AGENT = {"User-Agent": "Loyable/1.0 (local restaurant rewards app)"}


def normalize_address(address: str) -> str:
    text = (address or "").strip()
    replacements = [
        (r"\bKissimme\b", "Kissimmee"),
        (r"\bKissimee\b", "Kissimmee"),
        (r"\bHwy\b", "Highway"),
        (r"\bFL\b", "Florida"),
        (r",?\s*United States\s*$", ""),
        (r",?\s*USA\s*$", ""),
        (r"\s+", " "),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text.strip(" ,")


def _census_geocode(address: str):
    """
    US Census Bureau geocoder — best free option for exact US house numbers.
    Returns (lat, lng, matched_address) or (None, None, None).
    """
    address = normalize_address(address)
    if not address:
        return None, None, None

    params = urllib.parse.urlencode(
        {
            "address": address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        }
    )
    url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?{params}"
    req = urllib.request.Request(url, headers=USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
    except Exception:
        return None, None, None

    matches = (payload.get("result") or {}).get("addressMatches") or []
    if not matches:
        return None, None, None

    match = matches[0]
    coords = match.get("coordinates") or {}
    lng = coords.get("x")
    lat = coords.get("y")
    if lat is None or lng is None:
        return None, None, None
    return float(lat), float(lng), match.get("matchedAddress") or address


def _nominatim_search(query: str, limit: int = 1):
    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": limit,
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers=USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return []


def _query_variants(address: str):
    original = (address or "").strip()
    normalized = normalize_address(original)
    variants = []
    for value in (original, normalized):
        if value and value not in variants:
            variants.append(value)

    no_dir = re.sub(r"^(\d+)\s+[ENSW]\.?\s+", r"\1 ", normalized, flags=re.IGNORECASE)
    if no_dir and no_dir not in variants:
        variants.append(no_dir)

    return variants


def geocode_address(address: str):
    """Prefer Census (exact US house #), then fall back to OpenStreetMap."""
    for query in _query_variants(address):
        lat, lng, _matched = _census_geocode(query)
        if lat is not None:
            return lat, lng

    for query in _query_variants(address):
        data = _nominatim_search(query, limit=3)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None


def _format_photon_label(props: dict) -> str:
    parts = []
    housenumber = props.get("housenumber")
    street = props.get("street") or props.get("name")
    if housenumber and street:
        parts.append(f"{housenumber} {street}")
    elif street:
        parts.append(street)
    elif props.get("name"):
        parts.append(props["name"])

    for key in ("city", "town", "village", "state", "postcode", "country"):
        value = props.get(key)
        if value and value not in parts:
            parts.append(str(value))
    return ", ".join(parts)


def _photon_suggest(query: str, limit: int = 6):
    params = urllib.parse.urlencode({"q": query, "limit": limit, "lang": "en"})
    url = f"https://photon.komoot.io/api/?{params}"
    req = urllib.request.Request(url, headers=USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode())
    except Exception:
        return []

    suggestions = []
    seen = set()
    for feature in payload.get("features") or []:
        props = feature.get("properties") or {}
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        label = _format_photon_label(props)
        if not label or label in seen:
            continue
        seen.add(label)
        suggestions.append(
            {
                "label": label,
                "lat": float(coords[1]),
                "lng": float(coords[0]),
            }
        )
    return suggestions


def _looks_like_full_street_address(query: str) -> bool:
    """True when query has a house number and enough location text."""
    q = (query or "").strip()
    return bool(re.match(r"^\d+\s+\S+", q)) and len(q) >= 12


def suggest_addresses(query: str, limit: int = 6):
    """Autocomplete: Census first for house numbers, Photon for partial typing."""
    query = (query or "").strip()
    if len(query) < 3:
        return []

    suggestions = []
    seen = set()

    # When it looks like a real street address, Census can return the exact #2482
    if _looks_like_full_street_address(query):
        for candidate in _query_variants(query):
            lat, lng, matched = _census_geocode(candidate)
            if lat is None:
                continue
            label = matched or candidate
            key = label.lower()
            if key not in seen:
                seen.add(key)
                suggestions.append({"label": label, "lat": lat, "lng": lng})
            break

    normalized = normalize_address(query)
    for item in _photon_suggest(query, limit=limit) + _photon_suggest(normalized, limit=limit):
        key = item["label"].lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(item)

    return suggestions[:limit]
