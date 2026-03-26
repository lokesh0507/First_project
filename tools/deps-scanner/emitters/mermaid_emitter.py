def to_mermaid(edges: list[dict]) -> str:
    """
    Convert edges into Mermaid diagram text.
   
    Example output:
        graph LR
          service-a -->|REST| service-b
    """
 
    lines = ["graph LR"]  # Left-to-right graph
 
    for e in edges:
        src = e["src"]
        dst = e["dst"]
        label = e.get("method", e.get("type", "REST"))
 
        lines.append(f'  {src} -->|{label}| {dst}')
 
    return "\n".join(lines)