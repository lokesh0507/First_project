import pathlib

import re
 
from detectors.http_dotnet import find_http_edges

from resolvers.url_to_service import resolve

from emitters.mermaid_emitter import to_mermaid
 
# ✅ Kafka regex patterns
 
# ===========================
# KAFKA PRODUCER PATTERNS
# ===========================

# ProduceAsync("topic-name", message)
KAFKA_PRODUCER_ASYNC_RE = re.compile(
    r'ProduceAsync\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# Produce("topic-name", message, deliveryHandler)
KAFKA_PRODUCER_SYNC_RE = re.compile(
    r'(?<!Async\()Produce\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# ===========================
# KAFKA CONSUMER PATTERNS
# ===========================

# Subscribe("topic-name")  ← single topic
KAFKA_CONSUMER_SINGLE_RE = re.compile(
    r'Subscribe\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# Subscribe(new List<string> { "topic-1", "topic-2" })  ← multiple topics
KAFKA_CONSUMER_MULTI_RE = re.compile(
    r'Subscribe\(\s*new\s+List<string>\s*\{([^}]+)\}',
    re.IGNORECASE
)

# Subscribe(new[] { "topic-1", "topic-2" })  ← array style
KAFKA_CONSUMER_ARRAY_RE = re.compile(
    r'Subscribe\(\s*new\[\]\s*\{([^}]+)\}',
    re.IGNORECASE
)

# Assign(new TopicPartition("topic-name", ...))  ← manual partition
KAFKA_CONSUMER_ASSIGN_RE = re.compile(
    r'TopicPartition\(\s*"(?P<topic>[^"]+)"',
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

        # ✅ Producer: ProduceAsync
        for match in KAFKA_PRODUCER_ASYNC_RE.finditer(content):
            topic = match.group("topic")
            edges.append({
                "src": service_name,
                "dst": f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER"
            })

        # ✅ Producer: Produce (sync)
        for match in KAFKA_PRODUCER_SYNC_RE.finditer(content):
            topic = match.group("topic")
            edges.append({
                "src": service_name,
                "dst": f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER"
            })

        # ✅ Consumer: Subscribe single topic
        for match in KAFKA_CONSUMER_SINGLE_RE.finditer(content):
            topic = match.group("topic")
            edges.append({
                "src": f"Kafka:{topic}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER"
            })

        # ✅ Consumer: Subscribe multiple topics (List)
        for match in KAFKA_CONSUMER_MULTI_RE.finditer(content):
            topics_raw = match.group(1)
            topics = re.findall(r'"([^"]+)"', topics_raw)
            for topic in topics:
                edges.append({
                    "src": f"Kafka:{topic}",
                    "dst": service_name,
                    "type": "KAFKA_CONSUMER"
                })

        # ✅ Consumer: Subscribe multiple topics (Array)
        for match in KAFKA_CONSUMER_ARRAY_RE.finditer(content):
            topics_raw = match.group(1)
            topics = re.findall(r'"([^"]+)"', topics_raw)
            for topic in topics:
                edges.append({
                    "src": f"Kafka:{topic}",
                    "dst": service_name,
                    "type": "KAFKA_CONSUMER"
                })

        # ✅ Consumer: Assign (manual partition)
        for match in KAFKA_CONSUMER_ASSIGN_RE.finditer(content):
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

    all_services = []
 
    # ✅ 1. Scan LOCAL services (existing)

    services_root = pathlib.Path("services")

    if services_root.exists():

        print("📌 Auto-detecting services from /services directory...")

        local_services = discover_services(services_root)

        all_services.extend(local_services)

        print(f"✅ Found {len(local_services)} local services")

    else:

        print("⚠️ services/ directory not found, skipping local scan")
 
    # ✅ 2. Scan CLONED repos (NEW — Repo-1, Repo-2 etc.)

    repos_root = pathlib.Path("repos")

    if repos_root.exists():

        print("\n📌 Auto-detecting services from /repos directory...")

        repo_services = discover_services(repos_root)

        all_services.extend(repo_services)

        print(f"✅ Found {len(repo_services)} external services")

    else:

        print("⚠️ repos/ directory not found, skipping external scan")
 
    # ✅ 3. Check if any services found

    if not all_services:

        print("❌ No services found in services/ or repos/")

        return
 
    print(f"✅ Total services found: {len(all_services)}")

    for s in all_services:

        print(f"   • {s['name']}")
 
    all_edges = []
 
    print("\n🔍 Scanning dependencies (REST + Kafka)...")
 
    for svc in all_services:

        svc_name = svc["name"]

        svc_path = svc["path"]
 
        print(f"  ➜ Scanning {svc_name}...")
 
        # ✅ REST dependency detection (existing logic)

        rest_edges = find_http_edges(svc_name, svc_path)
 
        for e in rest_edges:

            dst_service = resolve(e["dst_url"], all_services)
 
            if dst_service != "UNKNOWN":

                all_edges.append({

                    "src": svc_name,

                    "dst": dst_service,

                    "method": e["method"],

                    "endpoint": e["endpoint"],

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

            e.get("method", e["type"]),

            e.get("endpoint", "")

        )

        if key not in seen:

            seen.add(key)

            unique_edges.append(e)
 
    all_edges = unique_edges
 
    print("🛠 Generating Mermaid diagram...")
 
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
 
    if html_template_path.exists():

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

    else:

        print("⚠️ HTML template not found, skipping HTML generation")
 
 
if __name__ == "__main__":

    main()
 