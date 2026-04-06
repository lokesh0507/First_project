import pathlib
import re

from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve
from emitters.mermaid_emitter import to_mermaid


# ✅ Kafka regex patterns

# Kafka Producer: ProduceAsync("topic-name")
KAFKA_PRODUCER_RE = re.compile(
    r'ProduceAsync\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# Kafka Consumer: Subscribe("topic-name")
KAFKA_CONSUMER_RE = re.compile(
    r'Subscribe\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)


# ✅ Kafka dependency detection

def find_kafka_edges(service_name: str, root_path: pathlib.Path):
    """
    Scan .cs files to detect Kafka producers and consumers.
    Kafka topics are normalized as Kafka:<topic-name>.
    """
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue

        # ✅ Kafka Producer: service -> Kafka:topic
        for match in KAFKA_PRODUCER_RE.finditer(content):
            topic = match.group("topic")
            edges.append({
                "src": service_name,
                "dst": f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER"
            })

        # ✅ Kafka Consumer: Kafka:topic -> service
        for match in KAFKA_CONSUMER_RE.finditer(content):
            topic = match.group("topic")
            edges.append({
                "src": f"Kafka:{topic}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER"
            })

    return edges


# ✅ Service discovery

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


# ✅ Main scanner

def main():
    print("📌 Auto-detecting services from /services directory...")

    services_root = pathlib.Path("services")

    if not services_root.exists():
        print("❌ services/ directory not found")
        return

    services = discover_services(services_root)

    print(f"✅ Found {len(services)} services:")
    for s in services:
        print(f"   • {s['name']}")

    all_edges = []

    print("\n🔍 Scanning dependencies (REST + Kafka)...")

    for svc in services:
        svc_name = svc["name"]
        svc_path = svc["path"]

        print(f"  ➜ Scanning {svc_name}...")

        # ✅ REST dependency detection (existing logic)
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

        # ✅ Kafka dependency detection
        kafka_edges = find_kafka_edges(svc_name, svc_path)
        all_edges.extend(kafka_edges)

    # ✅ Deduplicate edges safely (REST + Kafka)
    seen = set()
    unique_edges = []

    for e in all_edges:
        key = (
            e["src"],
            e["dst"],
            e.get("method", e["type"])
        )
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