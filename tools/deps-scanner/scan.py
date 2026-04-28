import pathlib
import re

from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve_by_name
from emitters.mermaid_emitter import to_mermaid


# ──────────────────────────────────────────────
# ✅ EVENT CLASS DETECTION PATTERNS — PRODUCER
# ──────────────────────────────────────────────

# Producer: ProduceAsync<OrderCreatedEvent>(...)
EVENT_PRODUCE_GENERIC_RE = re.compile(
    r'(?:Produce|ProduceAsync|Publish|PublishAsync|Send|SendAsync)'
    r'\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)

# Producer: ProduceAsync("topic", new OrderCreatedEvent(...))
EVENT_PRODUCE_NEW_RE = re.compile(
    r'(?:Produce|ProduceAsync)\s*\([^)]*new\s+(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*[({]',
)

# Producer: new Message<string, OrderCreatedEvent>
EVENT_MESSAGE_GENERIC_RE = re.compile(
    r'Message\s*<[^,]+,\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)

# ✅ NEW — Producer: var orderEvent = new OrderCreatedEvent { ... }
# This matches your EXACT service-b pattern
EVENT_VAR_NEW_RE = re.compile(    r'var\s+\w+\s*=\s*new\s+(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*[\r\s]*\{',
    re.MULTILINE
)


# ──────────────────────────────────────────────
# ✅ EVENT CLASS DETECTION PATTERNS — CONSUMER
# ──────────────────────────────────────────────

# Consumer: IConsumer<OrderCreatedEvent>
EVENT_CONSUMER_INTERFACE_RE = re.compile(
    r'IConsumer\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)

# Consumer: IEventHandler<OrderCreatedEvent>
EVENT_HANDLER_INTERFACE_RE = re.compile(
    r'IEventHandler\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)

# Consumer: ConsumeContext<OrderCreatedEvent>
EVENT_CONSUME_CONTEXT_RE = re.compile(
    r'ConsumeContext\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)

# Consumer: Handle(OrderCreatedEvent message)
EVENT_HANDLE_METHOD_RE = re.compile(
    r'Handle\s*\(\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s+',
)

# ✅ NEW — Consumer: JsonSerializer.Deserialize<OrderCreatedEvent>
# This matches your EXACT service-d pattern
DESERIALIZE_RE = re.compile(
    r'JsonSerializer\.Deserialize\s*<\s*(?P<event>[A-Z][A-Za-z0-9]+(?:Event|Message|Command|Notification))\s*>',
)


# ──────────────────────────────────────────────
# ✅ KAFKA TOPIC PATTERNS
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
# ✅ EVENT EXTRACTION FUNCTIONS
# ──────────────────────────────────────────────

def extract_produced_events(content: str) -> set[str]:
    """
    Scan file content and return ONLY events being PRODUCED.

    Supports:
    1. ProduceAsync<OrderCreatedEvent>(...)
    2. ProduceAsync("topic", new OrderCreatedEvent())
    3. new Message<string, OrderCreatedEvent>
    4. var orderEvent = new OrderCreatedEvent { ... }  ← your service-b pattern
    """
    events = set()

    # Pattern 1 — ProduceAsync<OrderCreatedEvent>
    for match in EVENT_PRODUCE_GENERIC_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 2 — ProduceAsync("topic", new OrderCreatedEvent())
    for match in EVENT_PRODUCE_NEW_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 3 — Message<string, OrderCreatedEvent>
    for match in EVENT_MESSAGE_GENERIC_RE.finditer(content):
        events.add(match.group("event"))

    # ✅ Pattern 4 — var orderEvent = new OrderCreatedEvent { ... }
    # Only scan if file has ProduceAsync → avoids false positives
    if "ProduceAsync" in content or "Publish" in content:
        for match in EVENT_VAR_NEW_RE.finditer(content):
            events.add(match.group("event"))

    return events


def extract_consumed_events(content: str) -> set[str]:
    """
    Scan file content and return ONLY events being CONSUMED.

    Supports:
    1. IConsumer<OrderCreatedEvent>
    2. IEventHandler<OrderCreatedEvent>
    3. ConsumeContext<OrderCreatedEvent>
    4. Handle(OrderCreatedEvent message)
    5. JsonSerializer.Deserialize<OrderCreatedEvent>  ← your service-d pattern
    """
    events = set()

    # Pattern 1 — IConsumer<OrderCreatedEvent>
    for match in EVENT_CONSUMER_INTERFACE_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 2 — IEventHandler<OrderCreatedEvent>
    for match in EVENT_HANDLER_INTERFACE_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 3 — ConsumeContext<OrderCreatedEvent>
    for match in EVENT_CONSUME_CONTEXT_RE.finditer(content):
        events.add(match.group("event"))

    # Pattern 4 — Handle(OrderCreatedEvent message)
    for match in EVENT_HANDLE_METHOD_RE.finditer(content):
        events.add(match.group("event"))

    # ✅ Pattern 5 — JsonSerializer.Deserialize<OrderCreatedEvent>
    # Only scan if file has Subscribe → avoids false positives
    if "Subscribe" in content:
        for match in DESERIALIZE_RE.finditer(content):
            events.add(match.group("event"))

    return events


# ──────────────────────────────────────────────
# ✅ KAFKA DEPENDENCY SCANNER
# ──────────────────────────────────────────────

def find_kafka_edges(service_name: str, root_path: pathlib.Path):
    edges = []

    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue

        # ✅ Extract events from this file
        produced_events = extract_produced_events(content)
        consumed_events = extract_consumed_events(content)

        # # ✅ Debug output
        # if produced_events:
        #     print(f"      📤 [{service_name}] {file.name} → produced: {produced_events}")
        # if consumed_events:
        #     print(f"      📥 [{service_name}] {file.name} → consumed: {consumed_events}")

        # ✅ Format as comma separated string
        producer_event_label = ", ".join(sorted(produced_events)) if produced_events else ""
        consumer_event_label = ", ".join(sorted(consumed_events)) if consumed_events else ""

        # ──────────────────────────────────────
        # ✅ PRODUCER edges
        # ──────────────────────────────────────
        for match in KAFKA_PRODUCER_ASYNC_RE.finditer(content):
            topic = match.group("topic")
            edge  = {
                "src":  service_name,
                "dst":  f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER",
            }
            if producer_event_label:
                edge["events"] = producer_event_label
            # print(f"      🔗 PRODUCER edge → topic: {topic} | events: {producer_event_label or 'NONE'}")
            edges.append(edge)

        for match in KAFKA_PRODUCER_SYNC_RE.finditer(content):
            topic = match.group("topic")
            edge  = {
                "src":  service_name,
                "dst":  f"Kafka:{topic}",
                "type": "KAFKA_PRODUCER",
            }
            if producer_event_label:
                edge["events"] = producer_event_label
            edges.append(edge)

        # ──────────────────────────────────────
        # ✅ CONSUMER edges
        # ──────────────────────────────────────
        for match in KAFKA_CONSUMER_SINGLE_RE.finditer(content):
            topic = match.group("topic")
            edge  = {
                "src":  f"Kafka:{topic}",
                "dst":  service_name,
                "type": "KAFKA_CONSUMER",
            }
            if consumer_event_label:
                edge["events"] = consumer_event_label
            # print(f"      🔗 CONSUMER edge → topic: {topic} | events: {consumer_event_label or 'NONE'}")
            edges.append(edge)

        for match in KAFKA_CONSUMER_MULTI_RE.finditer(content):
            topics = re.findall(r'"([^"]+)"', match.group(1))
            for topic in topics:
                edge = {
                    "src":  f"Kafka:{topic}",
                    "dst":  service_name,
                    "type": "KAFKA_CONSUMER",
                }
                if consumer_event_label:
                    edge["events"] = consumer_event_label
                edges.append(edge)

        for match in KAFKA_CONSUMER_ARRAY_RE.finditer(content):
            topics = re.findall(r'"([^"]+)"', match.group(1))
            for topic in topics:
                edge = {
                    "src":  f"Kafka:{topic}",
                    "dst":  service_name,
                    "type": "KAFKA_CONSUMER",
                }
                if consumer_event_label:
                    edge["events"] = consumer_event_label
                edges.append(edge)

        for match in KAFKA_CONSUMER_ASSIGN_RE.finditer(content):
            topic = match.group("topic")
            edge  = {
                "src":  f"Kafka:{topic}",
                "dst":  service_name,
                "type": "KAFKA_CONSUMER",
            }
            if consumer_event_label:
                edge["events"] = consumer_event_label
            # print(f"      🔗 CONSUMER edge → topic: {topic} | events: {consumer_event_label or 'NONE'}")
            edges.append(edge)

    return edges


# ──────────────────────────────────────────────
# ✅ SERVICE DISCOVERY
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
# ✅ MAIN
# ──────────────────────────────────────────────

def main():
    all_services = []

    # ✅ Local services
    services_root = pathlib.Path("services")
    if services_root.exists():
        local_services = discover_services(services_root)
        for svc in local_services:
            svc["repo"] = "First_project"
        all_services.extend(local_services)

    # ✅ External repos
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

    # ✅ REST dependencies
    print("🔍 Scanning REST dependencies...")
    for svc in all_services:
        print(f"→ Scanning {svc['name']}...")
        rest_edges = find_http_edges(svc["name"], svc["path"])
        for e in rest_edges:
            dst = resolve_by_name(e["dst_url"], all_services)
            if dst != "UNKNOWN" and dst != svc["name"]:
                all_edges.append({
                    "src":      svc["name"],
                    "dst":      dst,
                    "method":   e["method"],
                    "endpoint": e["endpoint"],
                    "type":     "REST",
                })

    # ✅ Kafka dependencies
    print("🔍 Scanning Kafka dependencies...")
    for svc in all_services:
        all_edges.extend(find_kafka_edges(svc["name"], svc["path"]))

    # ✅ Deduplicate edges
    seen         = set()
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

    # ✅ Build repo map
    repo_map = {svc["name"]: svc["repo"] for svc in all_services}
    for e in unique_edges:
        if e["src"].startswith("Kafka:"):
            repo_map[e["src"]] = "Kafka"
        if e["dst"].startswith("Kafka:"):
            repo_map[e["dst"]] = "Kafka"

    # ✅ Generate Mermaid
    mermaid = to_mermaid(unique_edges, repo_map)

    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)

    md_file = output_dir / "deps.md"
    md_file.write_text(mermaid, encoding="utf-8")
    print(f"✅ Dependency graph generated → {md_file}")

    # ✅ HTML Output
    template = pathlib.Path("tools/deps-scanner/templates/graph.html")
    html_out = output_dir / "deps.html"

    if template.exists():
        clean = mermaid.replace("```mermaid", "").replace("```", "").strip()
        html  = template.read_text().replace("{{GRAPH}}", clean)
        html_out.write_text(html, encoding="utf-8")
        print(f"✅ Interactive graph generated → {html_out}")


if __name__ == "__main__":
    main()