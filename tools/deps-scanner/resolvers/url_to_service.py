import re

# ✅ SINGLE SOURCE OF TRUTH
# Port number → Service name
SERVICE_PORTS = {
    5000: "service-a",
    5125: "service-b",
    5200: "service-c",
    5300: "service-d",
    5292: "service-e",
    5006: "service-f",
    5141: "service-g",
}

def resolve(url: str, services: list):
    """
    Resolve dependency ONLY using localhost:PORT.
    - No config
    - No service-name host
    - No guessing
    """

    # Extract port number from URL
    match = re.search(r":(\d+)", url)
    if not match:
        return "UNKNOWN"

    port = int(match.group(1))
    return SERVICE_PORTS.get(port, "UNKNOWN")