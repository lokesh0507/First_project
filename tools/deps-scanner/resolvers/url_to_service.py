# url_to_service.py

import re
from urllib.parse import urlparse


def extract_hostname(url: str) -> str:
    """
    Extract hostname from a URL.

    http://service-b/api/items                        → service-b
    http://service-b:8080/api/items                   → service-b
    http://service-b.namespace.svc.cluster.local/api  → service-b.namespace.svc.cluster.local
    http://localhost:5125/api/items                    → localhost
    """
    try:
        parsed = urlparse(url)
        # netloc = "service-b:8080" or "service-b"
        # hostname strips the port
        return parsed.hostname or ""
    except Exception:
        return ""


def resolve(url: str, port_map: dict) -> str:
    """
    Kept for backward compatibility.
    Production should use resolve_by_name() instead.
    """
    return resolve_by_name(url, list(port_map.values()) if port_map else [])


def resolve_by_name(url: str, services: list) -> str:
    """
    Resolve a URL to a service name by matching hostname
    against known service names.

    Uses LONGEST MATCH to avoid:
    - "service-f" matching before "service-f-extra"
    - "service-a" matching before "service-a-v2"

    Examples:
    url = "http://service-b/api/items"
    services = [{"name": "service-a"}, {"name": "service-b"}]
    returns  = "service-b"

    url = "http://service-b.namespace.svc.cluster.local/api"
    returns  = "service-b"   ← matches partial hostname

    url = "http://localhost:5125/api"
    returns  = "UNKNOWN"     ← localhost never matches a service name
    """
    if not url:
        return "UNKNOWN"

    hostname = extract_hostname(url)

    if not hostname:
        return "UNKNOWN"

    # ✅ Skip localhost / 127.0.0.1 — not a service name
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        print(f"      ⚠️ Skipping localhost URL — not resolvable by name: {url}")
        return "UNKNOWN"

    # ✅ Collect all service names
    service_names = [svc["name"] for svc in services]

    # ✅ Find all matches — hostname contains service name
    # Use LONGEST MATCH to avoid partial mismatches
    matches = [
        name for name in service_names
        if name.lower() in hostname.lower()
    ]

    if not matches:
        print(f"      ⚠️ No service matched hostname: {hostname} → URL: {url}")
        return "UNKNOWN"

    # ✅ Return LONGEST match to avoid wrong short match
    # "service-f" vs "service-f-extra" → picks "service-f-extra" if hostname has it
    best_match = max(matches, key=len)

    # print(f"      ✅ Resolved: {hostname} → {best_match}")
    return best_match