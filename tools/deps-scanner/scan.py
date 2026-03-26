
SERVICE_PORTS = {
    5000: "service-a",
    5125: "service-b",
    5200: "service-c"
}


import pathlib
from detectors.http_dotnet import find_http_edges
from resolvers.url_to_service import resolve
from emitters.mermaid_emitter import to_mermaid


def main():
    print("📌 Auto‑detecting services from /services directory...")

    services_root = pathlib.Path("services")
    services = []

    # ✅ Auto discover microservice folders (ServiceA, ServiceB, ServiceC...)
    for svc in services_root.iterdir():
        if svc.is_dir():
            services.append({
                "name": svc.name,
                "path": str(svc)
            })

    print(f"✅ Found {len(services)} services:")
    for s in services:
        print(f"   • {s['name']}")

    all_edges = []

    print("\n🔍 Scanning REST HTTP dependencies...")

    # ✅ Scan each service for HTTP calls
    for svc in services:
        svc_name = svc["name"]
        svc_path = pathlib.Path(svc["path"])

        print(f"  ➜ Scanning {svc_name} ...")

        rest_edges = find_http_edges(svc_name, svc_path)

        for e in rest_edges:
            # Resolve URL → service name (based on ports)
            dst = resolve(e["dst_url"], services)

            all_edges.append({
                "src": svc_name,
                "dst": dst,
                "method": e["method"],
                "type": "REST"
            })

    print("\n🛠 Generating Mermaid diagram...")

    mermaid_text = to_mermaid(all_edges)

    output_file = pathlib.Path("output/deps.mmd")
    output_file.write_text(mermaid_text, encoding="utf-8")

    print("✅ Dependency graph generated successfully!")
    print(f"➡️  Output file: {output_file}")


if __name__ == "__main__":
    main()