def to_mermaid(edges: list[dict]) -> str:
    """
    Convert edges into a Mermaid diagram wrapped in ```mermaid 
    so GitHub can render it visually.
    """

    lines = ["```mermaid", "graph LR"]  # ✅ GitHub-compatible start

    for e in edges:
        src = e["src"]
        dst = e["dst"]
         # ✅ NEW: Build label with method + endpoint
        if e["type"] == "REST":
            method = e.get("method", "GET")
            endpoint = e.get("endpoint", "")
            label = f"{method} {endpoint}"
        else:
            # Kafka edges keep original label
            label = e.get("type", "KAFKA")
        # label = e.get("method", e.get("type", "REST"))

        # ✅ Mermaid syntax arrow
        lines.append(f'  {src} -->|{label}| {dst}')

    lines.append("```")  # ✅ Close code fence for GitHub

    return "\n".join(lines)