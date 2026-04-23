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
        # ✅ Circular distance — handles wrap around 360°
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
 
    START_HUE     = 60.0   # Start at Yellow-Green → far from Kafka pink
    hue_candidate = START_HUE
 
    for repo in sorted_repos:
        # ✅ Keep advancing until safe hue found
        attempts = 0
        while is_hue_reserved(hue_candidate):
            hue_candidate += GOLDEN_ANGLE
            attempts += 1
            if attempts > 360:
                break  # safety fallback
 
        hue    = (hue_candidate % 360) / 360.0
        colour = hsl_to_hex(hue, 0.60, 0.70)
 
        repo_colour_map[repo] = colour
 
        # ✅ Advance for next repo
        hue_candidate += GOLDEN_ANGLE
 
    return repo_colour_map
 
 
def to_mermaid(edges: list[dict], repo_map: dict) -> str:
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
        lines.append(
            f'classDef {repo} fill:{colour},stroke:#333,color:#000'
        )
 
    # ✅ Collect all unique nodes
    all_nodes = set()
    for e in edges:
        all_nodes.add(e["src"])
        all_nodes.add(e["dst"])
 
    lines.append("")
 
    # ✅ Define nodes
    for node in sorted(all_nodes):
        repo_name = repo_map.get(node, "Unknown")
        label     = f"{node}{chr(10)}({repo_name})"
        lines.append(f'  {node}["{label}"]')
 
    lines.append("")
 
    # ✅ Draw edges
    for e in edges:
        src = e["src"]
        dst = e["dst"]
 
        if e["type"] == "REST":
            method   = e.get("method", "GET")
            endpoint = e.get("endpoint", "")
            label    = f"{method} {endpoint}".strip()
        else:
            label = e.get("type", "KAFKA")
 
        lines.append(f'  {src} -->|{label}| {dst}')
 
    # ✅ Apply colours
    kafka_nodes = [s for s, r in repo_map.items() if r == "Kafka"]
 
    if kafka_nodes:
        lines.append(f'class {",".join(kafka_nodes)} Kafka')
 
    for repo in repos:
        nodes = [s for s, r in repo_map.items() if r == repo]
        if nodes:
            lines.append(f'class {",".join(nodes)} {repo}')
 
    lines.append("```")
    return "\n".join(lines)
 