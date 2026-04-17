import re
import pathlib
from urllib.parse import urlparse
 
# ✅ HTTP method detection regex
HTTP_CALL_RE = re.compile(
    r'(GetAsync'
    r'|PostAsync'
    r'|PostAsJsonAsync'
    r'|PutAsync'
    r'|PutAsJsonAsync'
    r'|DeleteAsync'
    r'|PatchAsync'
    r'|PatchAsJsonAsync'
    r'|GetFromJsonAsync'
    r'|SendAsync'
    r'|GetStringAsync'
    r'|GetByteArrayAsync'
    r'|GetStreamAsync'
    r')\s*(<[^>]+>)?\s*\(\s*"(?P<url>http[^"]+)"',
    re.IGNORECASE
)
 
# ─────────────────────────────────────────────
# 📌 MAP METHOD TOKEN → CLEAN HTTP METHOD
#
# Fixes wrong method names like:
#   GetFromJsonAsync → GET  (not GETFROMJSON)
#   PostAsJsonAsync  → POST (not POSTASJSON)
#   PutAsJsonAsync   → PUT  (not PUTASJSON)
# ─────────────────────────────────────────────
METHOD_MAP = {
    "getasync":          "GET",
    "getfromjsonasync":  "GET",
    "getstringasync":    "GET",
    "getbytearrayasync": "GET",
    "getstreamasync":    "GET",
    "postasync":         "POST",
    "postasjsonasync":   "POST",
    "putasync":          "PUT",
    "putasjsonasync":    "PUT",
    "deleteasync":       "DELETE",
    "patchasync":        "PATCH",
    "patchasjsonasync":  "PATCH",
    "sendasync":         "SEND",
}
 
 
def resolve_http_method(method_token: str) -> str:
    """
    Converts method token to clean HTTP method name.
 
    Examples:
      GetAsync         → GET
      GetFromJsonAsync → GET
      PostAsJsonAsync  → POST
      PutAsJsonAsync   → PUT
    """
    key = method_token.strip().lower()
    return METHOD_MAP.get(key, method_token.replace("Async", "").upper())
 
 
def find_http_edges(service_name: str, root_path: pathlib.Path):
    """
    Scans .cs files under a service folder.
    Returns list of REST call edges.
    """
    edges = []
 
    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue
 
        for match in HTTP_CALL_RE.finditer(content):
            method_token = match.group(1)
 
            # ✅ Use METHOD_MAP for clean method names
            http_method = resolve_http_method(method_token)
 
            url = match.group("url")
 
            # ✅ Parse endpoint from URL
            parsed   = urlparse(url)
            endpoint = parsed.path if parsed.path else "/"
 
            edges.append({
                "src":      service_name,
                "dst_url":  url,
                "method":   http_method,    # ✅ Clean: "GET", "POST" etc.
                "endpoint": endpoint,       # ✅ Clean: "/items", "/health" etc.
                "type":     "REST"
            })
 
    return edges