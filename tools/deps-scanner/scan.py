import pathlib
import re
 
from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve_by_name
from emitters.mermaid_emitter import to_mermaid
 
 
# ============================================================
# REGEX PATTERNS
# ============================================================
 
# CloudEvent constant values
# Example:
# public const string BooksIngestRequestedV2 = "com.allegion.book.ingest.requested.v2";
CLOUD_EVENT_CONST_VALUE_RE = re.compile(
    r'public\s+const\s+string\s+(?P<name>\w+)\s*=\s*"(?P<value>[^"]+)"'
)
 
# Producer event type build calls
# Example:
# _cloudEventBuilder.Build(CloudEventConstants.EventTypes.BooksIngestRequestedV2, ...)
CLOUD_EVENT_BUILD_RE = re.compile(
    r'_cloudEventBuilder\s*\.\s*Build\s*\('
    r'\s*(?:CloudEventConstants\.EventTypes\.|EventTypes\.)'
    r'(?P<const>\w+)'
)
 
# Consumer event type dictionary
# Example:
# { EventTypes.BooksIngestedV2, HandleBooksIngestedAsync }
CONSUMER_EVENT_DICT_RE = re.compile(
    r'\{\s*(?:CloudEventConstants\.EventTypes\.|EventTypes\.)'
    r'(?P<const>\w+)\s*,\s*Handle\w+\s*\}'
)
 
# Consumer event type comparisons
# Example:
# string.Equals(cloudEvent.Type, CloudEventConstants.EventTypes.LibrariesLibraryCategoryAdded, ...)
CONSUMER_EVENT_EQUALS_RE = re.compile(
    r'(?:string\.Equals\s*\([^,]+,\s*|==\s*)'
    r'(?:CloudEventConstants\.EventTypes\.|EventTypes\.)'
    r'(?P<const>\w+)'
)
 
# Hosted consumer service class
# Example:
# class BooksConsumerService : HostedConsumerBaseClient<BooksConsumerCloudEventProcessor>
HOSTED_CONSUMER_BASE_RE = re.compile(
    r'class\s+\w+\s*:\s*HostedConsumerBaseClient\s*<\s*(?P<processor>\w+)\s*>'
)
 
# Message processor class
# Example:
# class BooksConsumerCloudEventProcessor : MessageProcessor
MESSAGE_PROCESSOR_CLASS_RE = re.compile(
    r'class\s+(?P<classname>\w+)\s*:\s*MessageProcessor'
)
 
# Generic options injection
OPTIONS_INJECTION_RE = re.compile(
    r'IOptions\s*<\s*(?P<optclass>[A-Z][A-Za-z0-9]+(?:Topic|Consumer)Options)\s*>'
)
 
# Hosted consumer options injection
HOSTED_CONSUMER_OPTIONS_RE = re.compile(
    r'IOptions\s*<\s*(?P<optclass>\w+(?:Consumer|Topic)Options)\s*>'
)
 
# Options Configs constant
# Example:
# public const string Configs = "Books";
OPTIONS_CONFIGS_RE = re.compile(
    r'public\s+const\s+string\s+Configs\s*=\s*"(?P<section>[^"]+)"'
)
 
# Variable topic producer
# Example:
# ProduceWithResponseAsync(_booksTopic, ...)
PRODUCE_WITH_RESPONSE_RE = re.compile(
    r'ProduceWithResponseAsync\s*\(\s*(?P<topicvar>\w+)\s*,',
    re.IGNORECASE
)
 
# Literal producer
KAFKA_PRODUCER_ASYNC_RE = re.compile(
    r'ProduceAsync\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)
 
KAFKA_PRODUCER_SYNC_RE = re.compile(
    r'(?<!With)Produce\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)
 
# Literal consumer
KAFKA_CONSUMER_SINGLE_RE = re.compile(
    r'Subscribe(?:\s*<[^>]+>)?\(\s*"(?P<topic>[^"]+)"',
    re.IGNORECASE
)
 
# Terraform topic values
# Example:
# kafka_topic_name_books = "books"
TFVARS_RE = re.compile(
    r'^\s*(?P<key>\w+)\s*=\s*"(?P<value>[^"]+)"',
    re.MULTILINE
)
 
# CI topic mapping
# Example:
# "kafka_topic_name_books": "booksTopicName"
CI_TOPIC_KEY_RE = re.compile(
    r'"kafka_topic_name_(?P<shortname>\w+)"\s*:\s*"(?P<varname>[^"]+)"'
)
 
 
# ============================================================
# SERVICE DISCOVERY
# ============================================================
 
def discover_services(root: pathlib.Path):
    """
    Discover services in a hybrid way.
 
    Rules:
    1. If a repo contains multiple Program.cs folders, treat each as its own service
       (dummy microservices repo case).
    2. If a repo contains exactly one Program.cs folder, treat that as the deployable
       service name, but scan the whole solution/repo root so related projects
       (.Application, .Services, etc.) are included (production repo case).
    """
    services = []
 
    # group by immediate child repo folder under root
    repo_dirs = [p for p in root.iterdir() if p.is_dir()]
 
    for repo_dir in repo_dirs:
        if "bin" in repo_dir.parts or "obj" in repo_dir.parts:
            continue
 
        program_dirs = []
 
        for path in repo_dir.rglob("*"):
            if not path.is_dir():
                continue
            if "bin" in path.parts or "obj" in path.parts:
                continue
            if (path / "Program.cs").exists():
                program_dirs.append(path)
 
        # Case 1: multiple Program.cs folders => each is a service
        if len(program_dirs) > 1:
            for prog_dir in program_dirs:
                services.append({
                    "name": prog_dir.name,
                    "path": prog_dir,
                })
 
        # Case 2: exactly one Program.cs folder => one deployable service
        elif len(program_dirs) == 1:
            prog_dir = program_dirs[0]
 
            # Prefer solution root if exists, so we catch Application/Services projects too
            sln_files = list(repo_dir.rglob("*.sln"))
            scan_path = sln_files[0].parent if sln_files else repo_dir
 
            services.append({
                "name": prog_dir.name,
                "path": scan_path,
            })
 
    return services
 
 
def find_api_project_name(sln_dir: pathlib.Path) -> str:
    """
    Find the API project name inside the solution.
    """
    for csproj in sln_dir.rglob("*.csproj"):
        if "api" in csproj.stem.lower():
            return csproj.stem
    return ""
 
# ============================================================
# TOPIC RESOLUTION
# ============================================================
 
def load_terraform_topics(root: pathlib.Path) -> dict:
    """
    Parse terraform.tfvars to get actual topic names.
    """
    topics = {}
 
    for tfvars_file in root.rglob("terraform.tfvars"):
        try:
            content = tfvars_file.read_text(errors="ignore")
        except Exception:
            continue
 
        for match in TFVARS_RE.finditer(content):
            key = match.group("key")
            value = match.group("value")
            if "kafka_topic" in key.lower():
                topics[key] = value
                print(f"   📋 Terraform topic found: {key} = {value}")
 
    return topics
 
 
def load_ci_topic_map(root: pathlib.Path) -> dict:
    """
    Parse CI yaml to map terraform output names to short topic names.
 
    Returns:
      { "booksTopicName": "books", "librariesTopicName": "libraries" }
    """
    varname_to_shortname = {}
 
    for yml_file in root.rglob("*.yml"):
        try:
            content = yml_file.read_text(errors="ignore")
        except Exception:
            continue
 
        for match in CI_TOPIC_KEY_RE.finditer(content):
            shortname = match.group("shortname")
            varname = match.group("varname")
            varname_to_shortname[varname] = shortname
 
    return varname_to_shortname
 
 
def build_section_to_topic_map(terraform_topics: dict, ci_varmap: dict) -> dict:
    """
    Build config section -> topic map.
 
    Example:
      Books -> books
      Libraries -> libraries
    """
    section_to_topic = {}
 
    for _, shortname in ci_varmap.items():
        tf_key = f"kafka_topic_name_{shortname}"
        topic_value = terraform_topics.get(tf_key)
        if topic_value:
            section_name = shortname.capitalize()
            section_to_topic[section_name] = topic_value
            print(f"   🔗 Section '{section_name}' -> topic '{topic_value}'")
 
    return section_to_topic
 
 
def find_options_config_section(options_class: str, roots: list[pathlib.Path]) -> str:
    """
    Find Configs section from options class.
 
    Examples:
      BooksTopicOptions      -> Books
      LibrariesTopicOptions  -> Libraries
    """
    for root in roots:
        for file in root.rglob("*.cs"):
            try:
                content = file.read_text(errors="ignore")
            except Exception:
                continue
 
            if options_class not in content:
                continue
 
            match = OPTIONS_CONFIGS_RE.search(content)
            if match:
                return match.group("section")
 
    return ""
 
 
# ============================================================
# CLOUD EVENT MAPS
# ============================================================
 
def build_cloud_event_const_map(roots: list[pathlib.Path]) -> dict:
    """
    Build:
      BooksIngestRequestedV2 -> com.allegion.book.ingest.requested.v2
    """
    const_map = {}
 
    for root in roots:
        for file in root.rglob("*.cs"):
            try:
                content = file.read_text(errors="ignore")
            except Exception:
                continue
 
            if "CloudEventConstants" not in content and "EventTypes" not in content:
                continue
 
            for match in CLOUD_EVENT_CONST_VALUE_RE.finditer(content):
                name = match.group("name")
                value = match.group("value")
                if "." in value:
                    const_map[name] = value
 
    return const_map
 
 
def build_processor_event_map(
    roots: list[pathlib.Path],
    cloud_event_const_map: dict
) -> dict:
    """
    Build:
      BooksConsumerCloudEventProcessor ->
        {
          "com.allegion.books.ingested.v2",
          "com.allegion.book.archived.v2"
        }
 
      LibrariesConsumerCloudEventProcessor ->
        {
          "com.allegion.libraries.librarycategory.added"
        }
    """
    processor_event_map = {}
 
    for root in roots:
        for file in root.rglob("*.cs"):
            try:
                content = file.read_text(errors="ignore")
            except Exception:
                continue
 
            class_match = MESSAGE_PROCESSOR_CLASS_RE.search(content)
            if not class_match:
                continue
 
            class_name = class_match.group("classname")
            event_types = set()
 
            for match in CONSUMER_EVENT_DICT_RE.finditer(content):
                const_name = match.group("const")
                resolved = cloud_event_const_map.get(const_name, const_name)
                event_types.add(resolved)
 
            for match in CONSUMER_EVENT_EQUALS_RE.finditer(content):
                const_name = match.group("const")
                resolved = cloud_event_const_map.get(const_name, const_name)
                event_types.add(resolved)
 
            if event_types:
                processor_event_map[class_name] = event_types
                print(f"   📦 Processor '{class_name}' handles: {event_types}")
 
    return processor_event_map
 
 
def build_producer_event_map(roots: list[pathlib.Path], cloud_event_const_map: dict) -> dict:
    producer_event_map = {}
 
    for root in roots:
        for file in root.rglob("*.cs"):
            try:
                content = file.read_text(errors="ignore")
            except Exception:
                continue
 
            event_types = set()
 
            for match in CLOUD_EVENT_BUILD_RE.finditer(content):
                const_name = match.group("const")
                resolved = cloud_event_const_map.get(const_name, const_name)
                event_types.add(resolved)
 
            if event_types:
                producer_event_map[file.stem] = event_types
                print(f"   📤 Producer handler '{file.stem}' produces: {event_types}")
 
    return producer_event_map
 
 
# ============================================================
# KAFKA EDGE DETECTION
# ============================================================
 
def find_kafka_edges(
    service_name: str,
    root_path: pathlib.Path,
    section_to_topic: dict,
    all_roots: list[pathlib.Path],
    processor_event_map: dict,
    producer_event_map: dict,
):
    edges = []
 
    # Precompute all producer event types once
    all_producer_events = set()
    for events in producer_event_map.values():
        all_producer_events.update(events)
    producer_event_label = ", ".join(sorted(all_producer_events)) if all_producer_events else ""
 
    for file in root_path.rglob("*.cs"):
        try:
            content = file.read_text(errors="ignore")
        except Exception:
            continue
 
        # ----------------------------------------------------
        # 1. Literal ProduceAsync("topic")
        # ----------------------------------------------------
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
 
        # ----------------------------------------------------
        # 2. Variable topic producer
        # ProduceWithResponseAsync(_booksTopic, ...)
        # ----------------------------------------------------
        if PRODUCE_WITH_RESPONSE_RE.search(content):
            found_topic = False
 
            for opt_match in OPTIONS_INJECTION_RE.finditer(content):
                opt_class = opt_match.group("optclass")
                section = find_options_config_section(opt_class, all_roots)
 
                if not section:
                    continue
 
                topic = section_to_topic.get(section)
                if not topic:
                    continue
 
                edge = {
                    "src": service_name,
                    "dst": f"Kafka:{topic}",
                    "type": "KAFKA_PRODUCER",
                }
                if producer_event_label:
                    edge["events"] = producer_event_label
                edges.append(edge)
                found_topic = True
                print(f"   ✅ Producer edge: {service_name} -> Kafka:{topic}")
 
            # Fallback for this codebase:
            # producer side uses BooksTopicOptions for _booksTopic
            if not found_topic:
                fallback_topic = section_to_topic.get("Books")
                if fallback_topic:
                    edge = {
                        "src": service_name,
                        "dst": f"Kafka:{fallback_topic}",
                        "type": "KAFKA_PRODUCER",
                    }
                    if producer_event_label:
                        edge["events"] = producer_event_label
                    edges.append(edge)
                    print(f"   ✅ Producer edge (fallback): {service_name} -> Kafka:{fallback_topic}")
 
        # ----------------------------------------------------
        # 3. Literal Subscribe("topic")
        # ----------------------------------------------------
        for match in KAFKA_CONSUMER_SINGLE_RE.finditer(content):
            topic = match.group("topic")
            edge = {
                "src": f"Kafka:{topic}",
                "dst": service_name,
                "type": "KAFKA_CONSUMER",
            }
            edges.append(edge)
 
        # ----------------------------------------------------
        # 4. HostedConsumerBaseClient pattern
        # BooksConsumerService : HostedConsumerBaseClient<BooksConsumerCloudEventProcessor>
        # LibrariesConsumerService : HostedConsumerBaseClient<LibrariesConsumerCloudEventProcessor>
        # ----------------------------------------------------
        hosted_match = HOSTED_CONSUMER_BASE_RE.search(content)
        if hosted_match:
            processor_class = hosted_match.group("processor")
            event_types = processor_event_map.get(processor_class, set())
            event_label = ", ".join(sorted(event_types)) if event_types else ""
 
            consumer_topics_added = set()
 
            for opt_match in HOSTED_CONSUMER_OPTIONS_RE.finditer(content):
                opt_class = opt_match.group("optclass")
                section = find_options_config_section(opt_class, all_roots)
 
                # Fallback mapping for consumer options classes that don't have Configs
                if not section:
                    lowered = opt_class.lower()
                    if "books" in lowered:
                        section = "Books"
                    elif "libraries" in lowered:
                        section = "Libraries"
 
                if not section:
                    continue
 
                topic = section_to_topic.get(section)
                if not topic:
                    continue
 
                edge = {
                    "src": f"Kafka:{topic}",
                    "dst": service_name,
                    "type": "KAFKA_CONSUMER",
                }
                if event_label:
                    edge["events"] = event_label
                edges.append(edge)
                consumer_topics_added.add(topic)
                print(f"   ✅ Consumer edge: Kafka:{topic} -> {service_name} events: {event_label}")
 
            # Extra fallback:
            # If HostedConsumerBaseClient exists and no topic was found from options,
            # infer from processor name
            if not consumer_topics_added:
                processor_lower = processor_class.lower()
 
                if "books" in processor_lower and "Books" in section_to_topic:
                    topic = section_to_topic["Books"]
                    edge = {
                        "src": f"Kafka:{topic}",
                        "dst": service_name,
                        "type": "KAFKA_CONSUMER",
                    }
                    if event_label:
                        edge["events"] = event_label
                    edges.append(edge)
                    print(f"   ✅ Consumer edge (fallback): Kafka:{topic} -> {service_name} events: {event_label}")
 
                elif "libraries" in processor_lower and "Libraries" in section_to_topic:
                    topic = section_to_topic["Libraries"]
                    edge = {
                        "src": f"Kafka:{topic}",
                        "dst": service_name,
                        "type": "KAFKA_CONSUMER",
                    }
                    if event_label:
                        edge["events"] = event_label
                    edges.append(edge)
                    print(f"   ✅ Consumer edge (fallback): Kafka:{topic} -> {service_name} events: {event_label}")
 
    return edges
 
 
# ============================================================
# MAIN
# ============================================================
 
def main():
    all_services = []
 
    # --------------------------------------------------------
    # 1. Scan local services folder
    # --------------------------------------------------------
    services_root = pathlib.Path("services")
    if services_root.exists():
        local_services = discover_services(services_root)
        for svc in local_services:
            svc["repo"] = "First_project"
        all_services.extend(local_services)
 
    # --------------------------------------------------------
    # 2. Scan cloned repos folder
    # --------------------------------------------------------
    repos_root = pathlib.Path("repos")
    if repos_root.exists():
        repo_services = discover_services(repos_root)
        for svc in repo_services:
            svc["repo"] = svc["path"].parts[1]
        all_services.extend(repo_services)
 
    if not all_services:
        print("❌ No services found")
        return
 
    print(f"\n✅ Services detected: {len(all_services)}")
    for svc in all_services:
        print(f"   -> {svc['name']} ({svc['path']})")
 
    # --------------------------------------------------------
    # 3. Build topic resolution map
    # --------------------------------------------------------
    print("\n🔍 Building Kafka topic resolution map...")
    terraform_topics = {}
    ci_varmap = {}
 
    for root in [services_root, repos_root]:
        if root.exists():
            terraform_topics.update(load_terraform_topics(root))
            ci_varmap.update(load_ci_topic_map(root))
 
    section_to_topic = build_section_to_topic_map(terraform_topics, ci_varmap)
 
    # Fallbacks for this codebase
    if "Books" not in section_to_topic:
        val = terraform_topics.get("kafka_topic_name_books", "books")
        section_to_topic["Books"] = val
        print(f"   🔁 Fallback: 'Books' -> '{val}'")
 
    if "Libraries" not in section_to_topic:
        val = terraform_topics.get("kafka_topic_name_libraries", "libraries")
        section_to_topic["Libraries"] = val
        print(f"   🔁 Fallback: 'Libraries' -> '{val}'")
 
    print(f"✅ Section -> Topic map: {section_to_topic}")
 
    # --------------------------------------------------------
    # 4. Collect all root paths
    # --------------------------------------------------------
    all_roots = [svc["path"] for svc in all_services]
 
    # --------------------------------------------------------
    # 5. Build cloud event maps
    # --------------------------------------------------------
    print("\n🔍 Building cloud event constant map...")
    cloud_event_const_map = build_cloud_event_const_map(all_roots)
    print(f"   ✅ Cloud event constants found: {len(cloud_event_const_map)}")
    for k, v in cloud_event_const_map.items():
        print(f"      {k} -> {v}")
 
    print("\n🔍 Building processor event map...")
    processor_event_map = build_processor_event_map(all_roots, cloud_event_const_map)
 
    print("\n🔍 Building producer event map...")
    producer_event_map = build_producer_event_map(all_roots, cloud_event_const_map)
 
    all_edges = []
 
    # --------------------------------------------------------
    # 6. Scan REST dependencies
    # --------------------------------------------------------
    print("\n🔍 Scanning REST dependencies...")
    for svc in all_services:
        print(f"   -> {svc['name']}...")
        rest_edges = find_http_edges(svc["name"], svc["path"])
 
        for edge in rest_edges:
            dst = resolve_by_name(edge["dst_url"], all_services)
            if dst != "UNKNOWN" and dst != svc["name"]:
                all_edges.append({
                    "src": svc["name"],
                    "dst": dst,
                    "method": edge["method"],
                    "endpoint": edge["endpoint"],
                    "type": "REST",
                })
 
    # --------------------------------------------------------
    # 7. Scan Kafka dependencies
    # --------------------------------------------------------
    print("\n🔍 Scanning Kafka dependencies...")
    for svc in all_services:
        print(f"   -> {svc['name']}...")
        kafka_edges = find_kafka_edges(
            svc["name"],
            svc["path"],
            section_to_topic,
            all_roots,
            processor_event_map,
            producer_event_map,
        )
        all_edges.extend(kafka_edges)
 
    # --------------------------------------------------------
    # 8. Deduplicate edges
    # --------------------------------------------------------
    seen = set()
    unique_edges = []
 
    for edge in all_edges:
        key = (
            edge["src"],
            edge["dst"],
            edge.get("method", edge["type"]),
            edge.get("endpoint", ""),
            edge.get("events", ""),
        )
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)
 
    print(f"\n✅ Total unique edges: {len(unique_edges)}")
    for edge in unique_edges:
        print(f"   {edge['src']} -> {edge['dst']} [{edge['type']}] events={edge.get('events', '')}")
 
    # --------------------------------------------------------
    # 9. Repo map for Mermaid
    # --------------------------------------------------------
    repo_map = {svc["name"]: svc["repo"] for svc in all_services}
 
    for edge in unique_edges:
        if edge["src"].startswith("Kafka:"):
            repo_map[edge["src"]] = "Kafka"
        if edge["dst"].startswith("Kafka:"):
            repo_map[edge["dst"]] = "Kafka"
 
    # --------------------------------------------------------
    # 10. Generate Mermaid output
    # --------------------------------------------------------
    mermaid = to_mermaid(unique_edges, repo_map)
 
    output_dir = pathlib.Path("output")
    output_dir.mkdir(exist_ok=True)
 
    md_file = output_dir / "deps.md"
    md_file.write_text(mermaid, encoding="utf-8")
    print(f"\n✅ Dependency graph -> {md_file}")
 
    # --------------------------------------------------------
    # 11. Generate HTML
    # --------------------------------------------------------
    template = pathlib.Path("tools/deps-scanner/templates/graph.html")
    html_out = output_dir / "deps.html"
 
    if template.exists():
        clean = mermaid.replace("```mermaid", "").replace("```", "").strip()
        html = template.read_text(encoding="utf-8").replace("{{GRAPH}}", clean)
        html_out.write_text(html, encoding="utf-8")
        print(f"✅ Interactive graph -> {html_out}")
 
 
if __name__ == "__main__":
    main()
 