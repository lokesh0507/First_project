# clone_repos.py
# ──────────────────────────────────────────────
# Auto discovers and clones repos from GitHub
# Simple rule: if repo name contains "iot"
# as a substring → clone it
# No hardcoded URLs needed
# ──────────────────────────────────────────────

import os
import subprocess
import requests
import pathlib

# ──────────────────────────────────────────────
# ✅ CONFIG
# ──────────────────────────────────────────────
GITHUB_USERNAME = "lokesh0507"
GITHUB_TOKEN    = os.environ.get("SCANNER_PAT")
FILTER_KEYWORD  = ".iot"                  # ← substring to search
CLONE_INTO      = pathlib.Path("repos")  # ← clone destination

# ──────────────────────────────────────────────
# ✅ GitHub API headers
# WHY: Needed to access private repos
# WHY: Without token only public repos visible
# ──────────────────────────────────────────────
HEADERS = {
    "Authorization":        f"Bearer {GITHUB_TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


def get_all_repos() -> list[dict]:
    """
    Fetch ALL repos from GitHub API
    Handles pagination automatically
    No hardcoded URLs needed ✅
    """
    repos    = []
    page     = 1
    per_page = 100

    print(f"🔍 Fetching repos for: {GITHUB_USERNAME}")

    while True:
        url = (
            f"https://api.github.com/user/repos"
            f"?per_page={per_page}"
            f"&page={page}"
            f"&type=all"
        )

        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"❌ GitHub API error: {response.status_code}")
            print(f"   {response.json().get('message', '')}")
            break

        page_repos = response.json()

        if not page_repos:
            break

        repos.extend(page_repos)
        page += 1
        print(f"   → Fetched page {page-1} ({len(page_repos)} repos)")

    print(f"✅ Total repos found: {len(repos)}")
    return repos


def filter_repos_by_keyword(
    repos:   list[dict],
    keyword: str
) -> list[dict]:
    """
    ✅ OPTION 2 — Simple substring match
    Rule: if repo name CONTAINS keyword anywhere → include it

    Case insensitive matching
    keyword = "iot"

    MATCHES:
    → allegion.iot        ✅ iot after dot
    → iot-sensor          ✅ iot at start
    → iot-dashboard       ✅ iot at start
    → allegion.iot-gw     ✅ iot in middle
    → my-iot-service      ✅ iot in middle
    → IOT-device          ✅ case insensitive

    SKIPS:
    → SharedKafka         ❌ no iot
    → Repo-1              ❌ no iot
    → allegion            ❌ no iot
    """

    # ✅ Simple substring check
    # keyword.lower() in repo["name"].lower()
    # → case insensitive
    # → matches anywhere in name
    filtered = [
        repo for repo in repos
        if keyword.lower() in repo["name"].lower()
    ]

    # ✅ Print what was found
    print(f"\n✅ Repos containing '{keyword}': {len(filtered)}")
    for repo in filtered:
        visibility = "🔒 private" if repo["private"] else "🌐 public"
        print(f"   → {repo['name']} ({visibility})")

    # ✅ Print what was skipped
    skipped = [
        repo for repo in repos
        if keyword.lower() not in repo["name"].lower()
    ]
    print(f"⏭️  Repos skipped (no '{keyword}'): {len(skipped)}")
    for repo in skipped:
        print(f"   → {repo['name']}")

    return filtered


def clone_repo(
    repo:       dict,
    clone_into: pathlib.Path
) -> None:
    """
    Clone a single repo
    If already exists → pull latest changes
    Uses token for private repo access ✅
    """
    repo_name = repo["name"]
    repo_url  = repo["clone_url"]

    # ✅ Inject token for private repo access
    # https://github.com/... → https://TOKEN@github.com/...
    auth_url = repo_url.replace(
        "https://",
        f"https://{GITHUB_TOKEN}@"
    )

    dest_path = clone_into / repo_name

    # ✅ Already cloned → pull latest
    if dest_path.exists():
        print(f"🔄 Already exists → pulling: {repo_name}")
        try:
            subprocess.run(
                ["git", "-C", str(dest_path), "pull"],
                check=True,
                capture_output=True
            )
            print(f"   ✅ Pulled latest: {repo_name}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Pull failed: {repo_name}")
            print(f"      {e.stderr.decode()}")
        return

    # ✅ Fresh clone
    print(f"📥 Cloning: {repo_name}")
    try:
        subprocess.run(
            ["git", "clone", auth_url, str(dest_path)],
            check=True,
            capture_output=True
        )
        print(f"   ✅ Cloned: {repo_name} → {dest_path}")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Clone failed: {repo_name}")
        print(f"      {e.stderr.decode()}")


def clone_filtered_repos(
    repos:      list[dict],
    clone_into: pathlib.Path
) -> None:
    """
    Clone all filtered repos into destination folder
    Creates folder if not exists
    """
    clone_into.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Cloning into: {clone_into.resolve()}")
    print("──────────────────────────────────────────")

    for repo in repos:
        clone_repo(repo, clone_into)

    print("──────────────────────────────────────────")
    print(f"✅ Done — {len(repos)} repos cloned/updated")


def main():
    # ✅ Check token set
    if not GITHUB_TOKEN:
        print("❌ SCANNER_PAT not set")
        print("   Windows: $env:SCANNER_PAT = 'your_token'")
        print("   Mac/Linux: export SCANNER_PAT='your_token'")
        return

    print("=" * 50)
    print(f"  Keyword filter : '{FILTER_KEYWORD}'")
    print(f"  Clone into     : {CLONE_INTO}")
    print(f"  GitHub user    : {GITHUB_USERNAME}")
    print("=" * 50)

    # ✅ Step 1 — Get ALL repos from GitHub
    all_repos = get_all_repos()

    # ✅ Step 2 — Filter repos containing "iot"
    iot_repos = filter_repos_by_keyword(
        all_repos,
        FILTER_KEYWORD
    )

    if not iot_repos:
        print(f"\n❌ No repos found containing '{FILTER_KEYWORD}'")
        return

    # ✅ Step 3 — Clone all filtered repos
    clone_filtered_repos(iot_repos, CLONE_INTO)


if __name__ == "__main__":
    main()