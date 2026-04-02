import re
import pathlib

# Regex to match:
#   GetAsync("http://service-b/items")
#   PostAsync("http://service-b/create")
#   PostAsJsonAsync("http://service-b/create", payload)
#   PutAsync("http://service-b/update")
#   DeleteAsync("http://service-b/delete")
HTTP_CALL_RE = re.compile(
    r'(GetAsync|PostAsync|PostAsJsonAsync|PutAsync|DeleteAsync)\(\s*"(?P<url>http[^"]+)"',
    re.IGNORECASE
)

def find_http_edges(service_name: str, root_path: pathlib.Path):
    """
    Scans .cs files under a service folder and returns a list of REST calls.

    Output format example:
    [
       {
         "src": "service-a",
         "dst_url": "http://service-b/items",
         "method": "POST",
         "type": "REST"
       }
    ]
    """
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue  # skip unreadable files

        for match in HTTP_CALL_RE.finditer(content):
            method_token = match.group(1)

            # Normalize method name
            if method_token.lower().startswith("post"):
                http_method = "POST"
            else:
                http_method = method_token.replace("Async", "").upper()

            url = match.group("url")

            edges.append({
                "src": service_name,
                "dst_url": url,
                "method": http_method,
                "type": "REST"
            })

    return edges