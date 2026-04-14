import yaml

import subprocess

import os
 
config_path = "tools/deps-scanner/config/deps.config.yaml"
 
with open(config_path, "r") as f:

    config = yaml.safe_load(f)
 
repos_dir = "repos"

os.makedirs(repos_dir, exist_ok=True)
 
# ✅ Read token from environment variable

token = os.environ.get("GH_PAT", "")
 
for repo in config["repositories"]:

    repo_url = repo["url"]
 
    # ✅ Inject token into URL for private repos

    if token:

        repo_url = repo_url.replace(

            "https://github.com",

            f"https://x-access-token:{token}@github.com"

        )
 
    repo_path = os.path.join(repos_dir, repo["name"])
 
    if os.path.exists(repo_path):

        print(f"Pulling latest for {repo['name']}...")

        subprocess.run(["git", "pull"], cwd=repo_path)

    else:

        print(f"Cloning {repo['name']}...")

        subprocess.run(["git", "clone", "-b", repo["branch"], repo_url, repo_path])
 