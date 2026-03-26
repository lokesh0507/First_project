import re

# ✅ Port → service mapping
SERVICE_PORTS = {
    5000: "service-a",
    5125: "service-b",
    5200: "service-c"
}

def resolve(url: str, services: list):
    """
    Resolve http://localhost:<port>/... to service name using SERVICE_PORTS.
    """

    # Extract port number from URL
    match = re.search(r":(\d+)", url)
    if not match:
        return url  # fallback for external URLs

    port = int(match.group(1))

    # ✅ Map port → service name
    if port in SERVICE_PORTS:
        return SERVICE_PORTS[port]

    # fallback: return the raw URL
    return url