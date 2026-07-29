import json
import urllib.parse
import urllib.request

NOMINATIM_HEADERS = {
    "User-Agent": "Loyable/1.0 (local restaurant rewards app)",
}


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
    req = urllib.request.Request(url, headers=NOMINATIM_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return []


def geocode_address(address: str):
    """Look up lat/lng for an address via OpenStreetMap Nominatim."""
    data = _nominatim_search(address, limit=1)
    if not data:
        return None, None
    return float(data[0]["lat"]), float(data[0]["lon"])


def suggest_addresses(query: str, limit: int = 5):
    """Return address autocomplete suggestions for a partial query."""
    query = (query or "").strip()
    if len(query) < 3:
        return []

    data = _nominatim_search(query, limit=limit)
    suggestions = []
    seen = set()
    for item in data:
        label = (item.get("display_name") or "").strip()
        if not label or label in seen:
            continue
        seen.add(label)
        suggestions.append(
            {
                "label": label,
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
            }
        )
    return suggestions
