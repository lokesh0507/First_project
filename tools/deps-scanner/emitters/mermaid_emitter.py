# ✅ 12 colours — supports up to 12 repos automatically
COLOURS = [
    "#87CEEB",  # Blue
    "#FFD700",  # Yellow
    "#90EE90",  # Green
    "#FFB6C1",  # Pink
    "#DDA0DD",  # Purple
    "#98FB98",  # Light Green
    "#FFA500",  # Orange
    "#FF6347",  # Tomato Red
    "#40E0D0",  # Turquoise
    "#EE82EE",  # Violet
    "#F0E68C",  # Khaki
    "#00CED1",  # Dark Turquoise
]

# ✅ Kafka always Pink
KAFKA_COLOUR = "#FFB6C1"

# ✅ First_project always Green
FIRST_PROJECT_COLOUR = "#90EE90"


def to_mermaid(edges: list[dict], repo_map: dict) -> str:
    lines = ["```mermaid", "graph LR"]

    # ✅ Separate repos and kafka
    repos = sorted(set(
        r for r in repo_map.values()
        if r != "Kafka" and r != "First_project"
    ))

    # ✅ Define First_project colour
    lines.append(
        f'classDef First_project fill:{FIRST_PROJECT_COLOUR},stroke:#333,color:#000'
    )

    # ✅ Define Kafka colour
    lines.append(
        f'classDef Kafka fill:{KAFKA_COLOUR},stroke:#333,color:#000'
    )

    # ✅ Auto-assign colours to each repo
    for i, repo in enumerate(repos):
        colour = COLOURS[i % len(COLOURS)]

        # skip green and pink (already used)
        if colour in (FIRST_PROJECT_COLOUR, KAFKA_COLOUR):
            colour = COLOURS[(i + 4) % len(COLOURS)]

        lines.append(
            f'classDef {repo} fill:{colour},stroke:#333,color:#000'
        )

    # ✅ Draw edges
    for e in edges:
        src = e["src"]
        dst = e["dst"]

        if e["type"] == "REST":
            method = e.get("method", "GET")
            endpoint = e.get("endpoint", "")
            label = f"{method} {endpoint}".strip()
        else:
            label = e.get("type", "KAFKA")

        # ✅ Correct Mermaid arrow
        lines.append(f'  {src} -->|{label}| {dst}')

    # ✅ Apply colours to nodes
    first_project_nodes = [s for s, r in repo_map.items() if r == "First_project"]
    kafka_nodes = [s for s, r in repo_map.items() if r == "Kafka"]

    if first_project_nodes:
        lines.append(f'class {",".join(first_project_nodes)} First_project')

    if kafka_nodes:
        lines.append(f'class {",".join(kafka_nodes)} Kafka')

    for repo in repos:
        nodes = [s for s, r in repo_map.items() if r == repo]
        if nodes:
            lines.append(f'class {",".join(nodes)} {repo}')

    lines.append("```")
    return "\n".join(lines)