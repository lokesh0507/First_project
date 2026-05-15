

# 📊 Microservice Dependency Graph Generator

A **fully automated dependency analysis tool** that scans .NET microservices across multiple repositories and generates a **visual dependency graph** (REST + Kafka) using Mermaid.

***
# 📦 Overview of the project:
This project is a Proof of Concept (POC) to automatically:
Discover microservice repositories from GitHub
Scan codebases for inter-service dependencies
Generate a visual dependency graph (REST + Kafka)
Eliminate manual dependency documentation
The system works by combining:
GitHub API-based repository onboarding
Static code analysis
Mermaid-based visualization
***

# 🚀 Features

✅ Automatic repository discovery and cloning  
✅ Scans **multiple repositories dynamically (no hardcoding)**  
✅ Detects:

 * REST API calls (`HttpClient`)
 * Kafka Producers & Consumers  
    ✅ Supports **private repos using GitHub PAT**  
    ✅ Generates:
 * 📄 `deps.md` (Mermaid graph)
 * 🌐 `deps.html` (interactive UI)  
    ✅ GitHub Actions CI integration  
    ✅ Avoids duplicate edges  
    ✅ Works with **real source code (no configs/manual mapping)**

***

# 🏗️ Project Structure

    FIRST_PROJECT/
    │
    ├── .github/workflows/
    │   └── generate-graph.yml      # GitHub Actions pipeline
    │
    ├── output/
    │   ├── deps.md                 # Mermaid graph
    │   └── deps.html               # Interactive graph
    │
    ├── tools/deps-scanner/
    │   ├── clone_repos.py          # Auto clone repos (based on keyword)
    │   ├── scan.py                 # Main scanner
    │   │
    │   ├── detectors/
    │   │   └── http_dotnet.py      # REST detection logic
    │   │
    │   ├── resolvers/
    │   │   └── url_to_service.py   # Resolves URL → service name
    │   │
    │   ├── emitters/
    │   │   └── mermaid_emitter.py  # Graph generation
    │   │
    │   └── templates/
    │       └── graph.html          # HTML template for graph
    │
    └── README.md

***

# ⚙️ How It Works

### 🔄 Full Flow

    1. Fetch repos from GitHub API
    2. Filter repositories (".iot" keyword)
    3. Clone repos locally
    4. Discover services
    5. Scan source code (.cs files)
    6. Detect:
       - REST calls
       - Kafka producers/consumers
    7. Build dependency edges
    8. Generate Mermaid graph
    9. Output HTML + MD files
    10. Commit back via GitHub Actions

***

# 🔍 What It Detects

## ✅ REST Dependencies

Example:

```csharp
await client.GetAsync("http://service-a/api/data");
```

➡ Generates:

    Service-B → Service-A  (GET /api/data)

***

## ✅ Kafka Dependencies

### Producer:

```csharp
ProduceAsync("order-created", ...)
```

➡

    Service-B → Kafka:order-created

***

### Consumer:

```csharp
Subscribe<OrderCreatedEvent>("order-created", ...)
```

➡

    Kafka:order-created → Service-D

***

# 📊 Output Example

    Service-B -->|GET /api| Service-A
    Service-B -->|KAFKA_PRODUCER| Kafka:order-created
    Kafka:order-created -->|KAFKA_CONSUMER| Service-D

***
# Graph Output
<img width="1891" height="678" alt="image (1)" src="https://github.com/user-attachments/assets/c9da383e-b048-45eb-ad01-29c861c18276" />

***

# 🤖 GitHub Actions Automation

### Triggers:

*    Push to `main`
*    Pull Request
*    External event (`repository_dispatch`)

***

### Workflow Steps:

1.  Checkout repository
2.  Setup Python & install dependencies
3.  Setup .NET
4.  Add GitHub NuGet source
5.  Clone `.iot` repositories
6.  Run dependency scanner
7.  Generate graph
8.  Commit results (`[skip ci]`)
9.  Upload artifacts

***

# 🔐 Setup (IMPORTANT)

## ✅ Add GitHub PAT

Set environment variable:

### Windows:

```powershell
$env:SCANNER_PAT="your_token"
```

### Linux/Mac:

```bash
export SCANNER_PAT=your_token
```

***

## ✅ GitHub Secrets (for Actions)

Add in repo:

    SCANNER_PAT

***

# ▶️ How to Run Locally

```bash
cd tools/deps-scanner

python clone_repos.py
python scan.py
```

***



# 🧠 Key Concepts Used

*    Static code analysis (Regex-based)
*    Microservice dependency mapping
*    Kafka event flow detection
*    REST API tracing
*    Graph generation (Mermaid)
*    CI/CD automation (GitHub Actions)

***

# ⚡ Advantages

*    No manual configuration  
*    Works across multiple repositories  
*    Dynamic service discovery  
*    Supports private repos  
*    Visual representation of system architecture  
*    Helps understand microservices quickly






