from urllib.parse import urlparse
 
def resolve(url: str, services: list):
    """
    Convert a URL like:
        http://service-b/items
    into a service name like:
        service-b
 
    Uses base_urls from deps.config.yaml.
    """
 
    # Extract host from URL
    parsed = urlparse(url)
    host = parsed.netloc.lower() if parsed.netloc else url.lower()
 
    # Match host with a known service base_url
    for svc in services:
        for base in svc.get("base_urls", []):
            if host in base:
                return svc["name"]  # return service name
 
    # If no match → return host (external)
    return host
 