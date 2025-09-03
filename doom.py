#!/usr/bin/env python3
import requests
import sys
from pathlib import Path

def load_repos(filename):
    """Load repo list from a text file"""
    path = Path(filename)
    if not path.exists():
        print(f"Error: {filename} not found.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def get_latest_release(repo):
    """Fetch the latest release version from GitHub API"""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name", "No tag")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def main():
    # Default to repos.txt if no argument is provided
    filename = sys.argv[1] if len(sys.argv) > 1 else "repos.txt"
    repos = load_repos(filename)

    print(f"Latest GitHub release versions (from {filename}):\n")
    for repo in repos:
        version = get_latest_release(repo)
        print(f"{repo:<35}  {version}")

if __name__ == "__main__":
    main()
