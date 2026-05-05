import pathlib
import re

from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve_by_name
from emitters.mermaid_emitter import to_mermaid


# ──────────────────────────────────────────────
# ✅ EVENT CLASS DETECTION PATTERNS — PRODUCER
# Focused only on SharedKafka / Confluent-style usage
# ──────────────────────────────────────────────

# Matches:
# ProduceAsync<OrderCreatedEvent>(...)
# Produce<OrderCreatedEvent>(...)
EVENT_PRODUCE_GENERIC_RE = re.compile(
    r'(?:Produce|ProduceAsync)\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+Event)\s*>'
)

# Matches:
# ProduceAsync("topic", new OrderCreatedEvent(...))
# Produce("topic", new OrderCreatedEvent(...))
EVENT_PRODUCE_NEW_RE = re.compile(
    r'(?:Produce|ProduceAsync)\s*\([^)]*new\s+(?P<event>[A-Z][A-Za-z0-9]+Event)\s*[({]'
)

# Matches:
# new Message<string, OrderCreatedEvent>
EVENT_MESSAGE_GENERIC_RE = re.compile(
    r'Message\s*<[^,]+,\s*(?P<event>[A-Z][A-Za-z0-9]+Event)\s*>'
)

# Matches:
# var orderEvent = new OrderCreatedEvent { ... }
# var paymentEvent = new PaymentInitiatedEvent { ... }
EVENT_VAR_NEW_RE = re.compile(
    r'var\s+\w+\s*=\s*new\s+(?P<event>[A-Z][A-Za-z0-9]+Event)\s*[\r\s]*\{',
    re.MULTILINE
)


# ──────────────────────────────────────────────
# ✅ EVENT CLASS DETECTION PATTERNS — CONSUMER
# Focused only on SharedKafka / Confluent-style usage
# ──────────────────────────────────────────────

# Matches:
# Subscribe<OrderCreatedEvent>("topic", ...)
EVENT_SUBSCRIBE_GENERIC_RE = re.compile(
    r'Subscribe\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+Event)\s*>\s*\(',
    re.IGNORECASE
)

# Matches:
# JsonSerializer.Deserialize<OrderCreatedEvent>(...)
# Useful if some services still use manual consumer logic
DESERIALIZE_RE = re.compile(
    r'JsonSerializer\.Deserialize\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+Event)\s*>'
)


# ──────────────────────────────────────────────
# ✅ KAFKA TOPIC DETECTION PATTERNS
# Supports SharedKafka wrapper calls
# ──────────────────────────────────────────────

# Matches:
# ProduceAsync("order-created-bd", ...)
KAFKA_PRODUCER_ASYNC_RE = re.compile(
    r'ProduceAsync\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# Matches:
# Produce("order-created-bd", ...)
KAFKA_PRODUCER_SYNC_RE = re.compile(
    r'Produce\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)

# Matches:
# Subscribe<OrderCreatedEvent>("order-created-bd", ...)
# Subscribe("order-created-bd")
KAFKA_CONSUMER_SINGLE_RE = re.compile(
    r'Subscribe(?:\s*<[^>]+>)?\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)


# ──────────────────────────────────────────────
# ✅ EXTRACT PRODUCED EVENTS
# Reads one .cs file and returns event names produced in that file
# ──────────────────────────────────────────────

def extract_produced_events(content: str) -> set[str]:
    events = set()

    # Pattern 1:
    # ProduceAsync<OrderCreatedEvent>(...)
    # Produce<OrderCreatedEvent>(...)
    for match in EVENT_PRODUCE_GENERIC_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 2:
    # ProduceAsync("topic", new OrderCreatedEvent(...))
    for match in EVENT_PRODUCE_NEW_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 3:
    # new Message<string, OrderCreatedEvent>
    for match in EVENT_MESSAGE_GENERIC_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 4:
    # var orderEvent = new OrderCreatedEvent { ... }
    # Only apply if file contains Produce / ProduceAsync
    if "ProduceAsync" in content or "Produce(" in content:
        for match in EVENT_VAR_NEW_RE.finditer(content):
            events.add(match.group("event"))

    return events


# ──────────────────────────────────────────────
# ✅ EXTRACT CONSUMED EVENTS
# Reads one .cs file and returns event names consumed in that file
# ──────────────────────────────────────────────

def extract_consumed_events(content: str) -> set[str]:
    events = set()

    # Pattern 1:
    # Subscribe<OrderCreatedEvent>("topic", ...)
    if "Subscribe" in content:
        for match in EVENT_SUBSCRIBE_GENERIC_RE.finditer(content):
            events.add(match.group("event"))

    # Pattern 2:
    # JsonSerializer.Deserialize<OrderCreatedEvent>(...)
    # Useful for older/manual consumers
    if "Deserialize" in content:
        for match in DESERIALIZE_RE.finditer(content):
            events.add(match.group("event"))

    return events


# ──────────────────────────────────────────────
# ✅ FIND KAFKA EDGES
# Builds producer and consumer edges for each service
# ──────────────────────────────────────────────

def find_kafka_edges(service_name: str, root_path: pathlib.Path):
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue

        # Extract event names from the current file
        produced_events = extract_produced_events(content)
        consumed_events = extract_consumed_events(content)

        # Convert set → display label
        producer_event_label = ", ".join(sorted(produced_events)) if produced_events else ""
        consumer_event_label = ", ".join(sorted(consumed_events)) if consumed_events else ""

        # ──────────────────────────────────────
        # ✅ PRODUCER edges
        # Example:
        # service-b → Kafka:order-created-bd
        # ──────────────────────────────────────
        for match in KAFKA_PRODUCER_ASYNC_RE.finditer(content):
            topic = match.group("topic")
            edge = {
                "src": service_name,
                "dst": f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER",
            }
            if producer_event_label:
                edge["events"] = producer_event_label
            edges.append(edge)

        for match in KAFKA_PRODUCER_SYNC_RE.finditer(content):
            topic = match.group("topic")
            edge = {
                "src": service_name,
                "dst": f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER",
            }
            if producer_event_label:
                edge["events"] = producer_event_label
            edges.append(edge)

        # ──────────────────────────────────────
        # ✅ CONSUMER edges
        # Example:
        # Kafka:order-created-bd → service-d
        # ──────────────────────────────────────
        for match in KAFKA_CONSUMER_SINGLE_RE.finditer(content):
            topic = match.group("topic")
            edge = {
                "src": f"Kafka:{topic}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER",
            }
            if consumer_event_label:
                edge["events"] = consumer_event_label
            edges.append(edge)

    return edges


# ──────────────────────────────────────────────
# ✅ DISCOVER SERVICES
# A folder is treated as a service if it contains:
# - Program.cs
# - appsettings.json
# - or any .csproj file
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
# ✅ MAIN ENTRY
# - discovers services
# - scans REST dependencies
# - scans Kafka dependencies
# - generates Mermaid + HTML output
# ──────────────────────────────────────────────

def main():
    all_services = []

    # ✅ Scan local services folder
    services_root = pathlib.Path("services")
    if services_root.exists():
        local_services = discover_services(services_root)
        for svc in local_services:
            svc["repo"] = "First_project"
        all_services.extend(local_services)

    # ✅ Scan repos folder
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

    # ✅ Scan REST dependencies
    print("🔍 Scanning REST dependencies...")
    for svc in all_services:
        print(f"→ Scanning {svc['name']}...")
        rest_edges = find_http_edges(svc["name"], svc["path"])
        for e in rest_edges:
            dst = resolve_by_name(e["dst_url"], all_services)
            if dst != "UNKNOWN" and dst != svc["name"]:
                all_edges.append({
                    "src": svc["name"],
                    "dst": dst,
                    "method": e["method"],
                    "endpoint": e["endpoint"],
                    "type": "REST",
                })

    # ✅ Scan Kafka dependencies
    print("🔍 Scanning Kafka dependencies...")
    for svc in all_services:
        all_edges.extend(find_kafka_edges(svc["name"], svc["path"]))

    # ✅ Remove duplicate edges
    seen = set()
    unique_edges = []
    for e in all_edges:
        key = (
            e["src"],
            e["dst"],
            e.get("method", e["type"]),
            e.get("endpoint", ""),
            e.get("events", "")
        )
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # ✅ Build repo map for Mermaid labels
    repo_map = {svc["name"]: svc["repo"] for svc in all_services}
    for e in unique_edges:
        if e["src"].startswith("Kafka:"):
            repo_map[e["src"]] = "Kafka"
        if e["dst"].startswith("Kafka:"):
            repo_map[e["dst"]] = "Kafka"

    # ✅ Generate Mermaid text
    mermaid = to_mermaid(unique_edges, repo_map)

    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)

    md_file = output_dir / "deps.md"
    md_file.write_text(mermaid, encoding="utf-8")
    print(f"✅ Dependency graph generated → {md_file}")

    # ✅ Generate HTML graph if template exists
    template = pathlib.Path("tools/deps-scanner/templates/graph.html")
    html_out = output_dir / "deps.html"

    if template.exists():
        clean = mermaid.replace("```mermaid", "").replace("```", "").strip()
        html = template.read_text().replace("{{GRAPH}}", clean)
        html_out.write_text(html, encoding="utf-8")
        print(f"✅ Interactive graph generated → {html_out}")


if __name__ == "__main__":
    main()