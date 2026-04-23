import pathlib
import re

from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve_by_name
from emitters.mermaid_emitter import to_mermaid


# ──────────────────────────────────────────────
# ✅ Kafka Regex Patterns
# ──────────────────────────────────────────────

KAFKA_PRODUCER_ASYNC_RE = re.compile(
    r'ProduceAsync\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

KAFKA_PRODUCER_SYNC_RE = re.compile(
    r'(?<!Async\()Produce\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

KAFKA_CONSUMER_SINGLE_RE = re.compile(
    r'Subscribe\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

KAFKA_CONSUMER_MULTI_RE = re.compile(
    r'Subscribe\(\s*new\s+List<string>\s*\{([^}]+)\}',
    re.IGNORECASE
)

KAFKA_CONSUMER_ARRAY_RE = re.compile(
    r'Subscribe\(\s*new\[\]\s*\{([^}]+)\}',
    re.IGNORECASE
)

KAFKA_CONSUMER_ASSIGN_RE = re.compile(
    r'TopicPartition\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)


# ──────────────────────────────────────────────
# ✅ Kafka Dependency Scanner
# ──────────────────────────────────────────────

def find_kafka_edges(service_name: str, root_path: pathlib.Path):
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue

        # Producer
        for match in KAFKA_PRODUCER_ASYNC_RE.finditer(content):
            edges.append({
                "src": service_name,
                "dst": f"Kafka:{match.group('topic')}",
                "type": "KAFKA_PRODUCER",
            })

        for match in KAFKA_PRODUCER_SYNC_RE.finditer(content):
            edges.append({
                "src": service_name,
                "dst": f"Kafka:{match.group('topic')}",
                "type": "KAFKA_PRODUCER",
            })

        # Consumer
        for match in KAFKA_CONSUMER_SINGLE_RE.finditer(content):
            edges.append({
                "src": f"Kafka:{match.group('topic')}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER",
            })

        for regex in (KAFKA_CONSUMER_MULTI_RE, KAFKA_CONSUMER_ARRAY_RE):
            for match in regex.finditer(content):
                topics = re.findall(r'"([^"]+)"', match.group(1))
                for topic in topics:
                    edges.append({
                        "src": f"Kafka:{topic}",
                        "dst": service_name,
                        "type": "KAFKA_CONSUMER",
                    })

        for match in KAFKA_CONSUMER_ASSIGN_RE.finditer(content):
            edges.append({
                "src": f"Kafka:{match.group('topic')}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER",
            })

    return edges


# ──────────────────────────────────────────────
# ✅ Service Discovery
# ──────────────────────────────────────────────

def discover_services(root: pathlib.Path):
    services = []

    for path in root.rglob("*"):
        if (
            not path.is_dir()
            or "bin" in path.parts
            or "obj" in path.parts
        ):
            continue

        has_indicator = (
            (path / "Program.cs").exists()
            or (path / "appsettings.json").exists()
            or any(path.glob("*.csproj"))
        )

        if has_indicator:
            services.append({
                "name": path.name,
                "path": path
            })

    return services


# ──────────────────────────────────────────────
# ✅ Main Scanner
# ──────────────────────────────────────────────

def main():
    all_services = []

    # ── Local services
    services_root = pathlib.Path("services")
    if services_root.exists():
        local_services = discover_services(services_root)
        for svc in local_services:
            svc["repo"] = "First_project"
        all_services.extend(local_services)

    # ── External repos
    repos_root = pathlib.Path("repos")
    if repos_root.exists():
        repo_services = discover_services(repos_root)
        for svc in repo_services:
            svc["repo"] = svc["path"].parts[1]
        all_services.extend(repo_services)

    if not all_services:
        print("❌ No services found")
        return

    print(f"✅ Services detected: {len(all_services)}")

    all_edges = []

    # ── REST dependencies (SERVICE NAME BASED ✅)
    print("🔍 Scanning REST dependencies...")
    for svc in all_services:
        print(f"→ Scanning {svc['name']}...")
        rest_edges = find_http_edges(svc["name"], svc["path"])
        for e in rest_edges:
            dst = resolve_by_name(e["dst_url"], all_services)
            if dst != "UNKNOWN" and dst !=svc["name"]:
                all_edges.append({
                    "src": svc["name"],
                    "dst": dst,
                    "method": e["method"],
                    "endpoint": e["endpoint"],
                    "type": "REST",
                })

    # ── Kafka dependencies
    print("🔍 Scanning Kafka dependencies...")
    for svc in all_services:
        all_edges.extend(find_kafka_edges(svc["name"], svc["path"]))

    # ── Deduplicate edges
    seen = set()
    unique_edges = []
    for e in all_edges:
        key = (
            e["src"],
            e["dst"],
            e.get("method", e["type"]),
            e.get("endpoint", "")
        )
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # ── Repo map
    repo_map = {svc["name"]: svc["repo"] for svc in all_services}
    for e in unique_edges:
        if e["src"].startswith("Kafka:"):
            repo_map[e["src"]] = "Kafka"
        if e["dst"].startswith("Kafka:"):
            repo_map[e["dst"]] = "Kafka"

    # ── Generate Mermaid
    mermaid = to_mermaid(unique_edges, repo_map)

    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)

    md_file = output_dir / "deps.md"
    md_file.write_text(mermaid, encoding="utf-8")

    print(f"✅ Dependency graph generated → {md_file}")

    # ── HTML Output
    template = pathlib.Path("tools/deps-scanner/templates/graph.html")
    html_out = output_dir / "deps.html"

    if template.exists():
        clean = mermaid.replace("```mermaid", "").replace("```", "").strip()
        html = template.read_text().replace("{{GRAPH}}", clean)
        html_out.write_text(html, encoding="utf-8")
        print(f"✅ Interactive graph generated → {html_out}")


if __name__ == "__main__":
    main()