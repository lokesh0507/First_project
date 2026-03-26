import yaml
import pathlib
 
from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve
from emitters.mermaid_emitter import to_mermaid
 
 
def main():
    print("📌 Loading config...")
 
    # Load YAML configuration
    config_path = pathlib.Path("tools/deps-scanner/config/deps.config.yaml")
    cfg = yaml.safe_load(config_path.read_text())
 
    services = cfg["services"]
 
    all_edges = []
 
    print("🔍 Scanning services...")
 
    # Iterate over services and run detectors
    for svc in services:
        svc_name = svc["name"]
        svc_path = pathlib.Path(svc["path"])
 
        print(f"  ➜ Scanning {svc_name}...")
 
        # REST detection
        rest_edges = find_http_edges(svc_name, svc_path)
 
        for e in rest_edges:
            # Convert URL → service name
            dst = resolve(e["dst_url"], services)
 
            all_edges.append({
                "src": svc_name,
                "dst": dst,
                "method": e["method"],
                "type": "REST"
            })
 
    print("🛠 Generating Mermaid diagram...")
 
    mermaid_text = to_mermaid(all_edges)
 
    output_file = pathlib.Path("output/deps.mmd")
    output_file.write_text(mermaid_text)
 
    print("✅ Dependency graph generated:")
    print(f"   -> {output_file}")
 
 
if __name__ == "__main__":
    main()