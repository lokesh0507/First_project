import pathlib

from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve
from emitters.mermaid_emitter import to_mermaid


def discover_services(root: pathlib.Path):
    """
    Recursively discover services.
    A directory is considered a service if it contains:
      - Program.cs OR
      - appsettings.json OR
      - a .csproj file
    """
    services = []

    for path in root.rglob("*"):
        if not path.is_dir():
            continue

        has_program = (path / "Program.cs").exists()
        has_appsettings = (path / "appsettings.json").exists()
        has_csproj = any(path.glob("*.csproj"))

        if has_program or has_appsettings or has_csproj:
            services.append({
                "name": path.name,
                "path": path
            })

    return services


def main():
    print("📌 Auto-detecting services from /services directory...")

    services_root = pathlib.Path("services")

    if not services_root.exists():
        print("❌ services/ directory not found")
        return

    # ✅ RECURSIVE SERVICE DISCOVERY (supports nested services)
    services = discover_services(services_root)

    print(f"✅ Found {len(services)} services:")
    for s in services:
        print(f"   • {s['name']}")

    all_edges = []

    print("\n🔍 Scanning REST HTTP dependencies...")

    for svc in services:
        svc_name = svc["name"]
        svc_path = svc["path"]

        print(f"  ➜ Scanning {svc_name}...")

        rest_edges = find_http_edges(svc_name, svc_path)

        for e in rest_edges:
            dst_service = resolve(e["dst_url"], services)

            if dst_service != "UNKNOWN":
                all_edges.append({
                    "src": svc_name,
                    "dst": dst_service,
                    "method": e["method"],
                    "type": "REST"
                })

    # ✅ Deduplicate edges
    seen = set()
    unique_edges = []

    for e in all_edges:
        key = (e["src"], e["dst"], e["method"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    all_edges = unique_edges

    print("\n🛠 Generating Mermaid diagram...")

    mermaid_text = to_mermaid(all_edges)

    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)

    # ✅ Write Markdown output
    output_file = output_dir / "deps.md"
    output_file.write_text(mermaid_text, encoding="utf-8")

    print("✅ Dependency graph generated successfully!")
    print(f"➡️  Output file: {output_file}")

    # ✅ Generate interactive HTML
    html_template_path = pathlib.Path("tools/deps-scanner/templates/graph.html")
    html_output_path = pathlib.Path("output/deps.html")

    html_template = html_template_path.read_text(encoding="utf-8")

    # ✅ Strip markdown fences for HTML rendering
    clean_mermaid = (
        mermaid_text
        .replace("```mermaid", "")
        .replace("```", "")
        .strip()
    )

    html_content = html_template.replace("{{GRAPH}}", clean_mermaid)

    html_output_path.write_text(html_content, encoding="utf-8")

    print(f"➡️ Interactive graph generated: {html_output_path}")


if __name__ == "__main__":
    main()
