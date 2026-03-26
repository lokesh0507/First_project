import re
import pathlib
 
# Regex to match:
#   GetAsync("http://service-b/items")
#   PostAsync("http://service-b/create")
#   PutAsync("http://service-b/update")
#   DeleteAsync("http://service-b/delete")
HTTP_CALL_RE = re.compile(
    r'(GetAsync|PostAsync|PutAsync|DeleteAsync)\(\s*"(?P<url>http[^"]+)"',
    re.IGNORECASE
)
 
def find_http_edges(service_name: str, root_path: pathlib.Path):
    """
    Scans .cs files under a service folder and returns a list of REST calls.
   
    Output format example:
    [
       { "src": "service-a", "dst_url": "http://service-b/items", "method": "GET" }
    ]
    """
    edges = []
 
    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except:
            continue  # skip unreadable files
 
        for match in HTTP_CALL_RE.finditer(content):
            http_method = match.group(1).replace("Async", "").upper()
            url = match.group("url")
 
            edges.append({
                "src": service_name,
                "dst_url": url,
                "method": http_method,
                "type": "REST"
            })
 
    return edges
 