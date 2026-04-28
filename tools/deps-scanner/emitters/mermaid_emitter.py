import hashlib
import colorsys

# ✅ Reserved colours
KAFKA_COLOUR = "#FFB6C1"  # Pink → always Kafka

# ✅ Golden angle
GOLDEN_ANGLE = 137.508

# ✅ Reserved hue ranges to SKIP — add more if needed!
RESERVED_HUES = [
    (340.0, 25.0),  # Kafka Pink range → skip ±25° around 340°
]


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL to HEX color string."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )


def is_hue_reserved(hue_degrees: float) -> bool:
    """
    Check if hue is too close to any reserved color.
    Circular distance used → handles 0°/360° wrap correctly!
    """
    for center_hue, tolerance in RESERVED_HUES:
        diff = abs(hue_degrees % 360 - center_hue)
        diff = min(diff, 360 - diff)
        if diff < tolerance:
            return True
    return False


def generate_colours_for_repos(repos: list) -> dict:
    """
    Generate maximally different colors for unlimited repos.

    ✅ Golden angle    → max color spread guaranteed
    ✅ Skip reserved   → never similar to Kafka or other reserved
    ✅ Unlimited repos → works for any number of repos!
    ✅ Sorted repos    → consistent color assignment always
    """
    sorted_repos    = sorted(repos)
    repo_colour_map = {}

    START_HUE     = 60.0
    hue_candidate = START_HUE

    for repo in sorted_repos:
        attempts = 0
        while is_hue_reserved(hue_candidate):
            hue_candidate += GOLDEN_ANGLE
            attempts += 1
            if attempts > 360:
                break

        hue    = (hue_candidate % 360) / 360.0
        colour = hsl_to_hex(hue, 0.60, 0.70)

        repo_colour_map[repo] = colour
        hue_candidate += GOLDEN_ANGLE

    return repo_colour_map


def sanitize_id(name: str) -> str:
    """
    Sanitize any name to be a valid Mermaid node ID or class name.

    Kafka:order-created-bd  →  Kafka_order_created_bd
    service-a               →  service_a
    Repo-1                  →  Repo_1
    """
    return (
        name
        .replace(":", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def is_valid_service(name: str) -> bool:
    """
    Filter out invalid entries like net8.0, net6.0 etc.
    """
    invalid_prefixes = ("net", "netstandard", "netcoreapp")
    lower = name.lower()
    for prefix in invalid_prefixes:
        if lower.startswith(prefix) and any(c.isdigit() for c in name):
            return False
    return True


def build_kafka_producer_label(events: str) -> str:
    """
    Build KAFKA_PRODUCER edge label with bullet points.
    Uses <br/> — safe for Mermaid edge labels.
    """
    if not events:
        return "KAFKA_PRODUCER"

    event_bullets = "<br/>".join(
        f"• {ev.strip()}"
        for ev in events.split(",")
        if ev.strip()
    )
    return f"KAFKA_PRODUCER<br/>Events Producing:<br/>{event_bullets}"


def build_kafka_consumer_label(events: str) -> str:
    """
    Build KAFKA_CONSUMER edge label with bullet points.
    Uses <br/> — safe for Mermaid edge labels.
    """
    if not events:
        return "KAFKA_CONSUMER"

    event_bullets = "<br/>".join(
        f"• {ev.strip()}"
        for ev in events.split(",")
        if ev.strip()
    )
    return f"KAFKA_CONSUMER<br/>Events Consuming:<br/>{event_bullets}"


def to_mermaid(edges: list[dict], repo_map: dict) -> str:

    # ✅ Filter out invalid service names like net8.0
    repo_map = {
        service: repo
        for service, repo in repo_map.items()
        if is_valid_service(service)
    }

    lines = ["```mermaid", "graph LR"]

    # ✅ Collect all repos (exclude Kafka)
    repos = sorted(set(
        r for r in repo_map.values()
        if r != "Kafka"
    ))

    # ✅ Generate maximally spread colors
    repo_colour_map = generate_colours_for_repos(repos)

    # ✅ Define Kafka colour
    lines.append(
        f'classDef Kafka fill:{KAFKA_COLOUR},stroke:#333,color:#000'
    )

    # ✅ Define repo colours
    for repo, colour in repo_colour_map.items():
        safe_repo = sanitize_id(repo)
        lines.append(
            f'classDef {safe_repo} fill:{colour},stroke:#333,color:#000'
        )

    # ✅ Collect all unique nodes
    all_nodes = set()
    for e in edges:
        all_nodes.add(e["src"])
        all_nodes.add(e["dst"])

    lines.append("")

    # ✅ Define nodes
    for node in sorted(all_nodes):
        safe_node = sanitize_id(node)
        repo_name = repo_map.get(node, "Unknown")
        label     = f"{node}{chr(10)}({repo_name})"
        lines.append(f'  {safe_node}["{label}"]')

    lines.append("")

    # ✅ Draw edges
    for e in edges:
        src    = sanitize_id(e["src"])
        dst    = sanitize_id(e["dst"])
        events = e.get("events", "")

        if e["type"] == "REST":
            method   = e.get("method", "GET")
            endpoint = e.get("endpoint", "")
            label    = f"{method} {endpoint}".strip()
            lines.append(f'  {src} -->|{label}| {dst}')

        elif e["type"] == "KAFKA_PRODUCER":
            label = build_kafka_producer_label(events)
            lines.append(f'  {src} -->|"{label}"| {dst}')

        elif e["type"] == "KAFKA_CONSUMER":
            label = build_kafka_consumer_label(events)
            lines.append(f'  {src} -->|"{label}"| {dst}')

        else:
            label = e.get("type", "KAFKA")
            lines.append(f'  {src} -->|{label}| {dst}')

    lines.append("")

    # ✅ Apply colours
    kafka_nodes = [
        sanitize_id(s)
        for s, r in repo_map.items()
        if r == "Kafka"
    ]
    if kafka_nodes:
        lines.append(f'class {",".join(sorted(kafka_nodes))} Kafka')

    for repo in repos:
        safe_repo = sanitize_id(repo)
        nodes     = [
            sanitize_id(s)
            for s, r in repo_map.items()
            if r == repo
        ]
        if nodes:
            lines.append(f'class {",".join(sorted(nodes))} {safe_repo}')

    lines.append("```")

    # ✅ FIX — use chr(10) explicitly — never gets corrupted when copying
    return chr(10).join(lines)