import re
import pathlib
from urllib.parse import urlparse

HTTP_CALL_RE = re.compile(
    r'(GetAsync|PostAsync|PostAsJsonAsync|PutAsync|DeleteAsync)\(\s*"(?P<url>http[^"]+)"',
    re.IGNORECASE
)

def find_http_edges(service_name: str, root_path: pathlib.Path):
    """
    Scans .cs files under a service folder and returns a list of REST calls.
    """
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue

        for match in HTTP_CALL_RE.finditer(content):
            method_token = match.group(1)

            if method_token.lower().startswith("post"):
                http_method = "POST"
            else:
                http_method = method_token.replace("Async", "").upper()

            url = match.group("url")              # ✅ "url" WITH QUOTES

            parsed = urlparse(url)                # ✅ Parse the URL
            endpoint = parsed.path if parsed.path else "/"

            edges.append({
                "src": service_name,
                "dst_url": url,
                "method": http_method,
                "endpoint": endpoint,
                "type": "REST"
            })

    return edges