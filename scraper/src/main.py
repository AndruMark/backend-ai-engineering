import os
import sys
from pathlib import Path
import requests

# Base configuration & Politeness headers
BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/AndruMark/backend-ai-engineering)"
REQUEST_TIMEOUT = 10  # seconds

# Resolve directories relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_page(url: str, cache_name: str) -> str:
    """
    Polite fetcher with local disk cache:
    - Reads from cache if present (CACHE HIT)
    - Otherwise performs HTTP GET with custom User-Agent, timeout, and status check (FETCH)
    """
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        content = cache_path.read_text(encoding="utf-8")
        size_bytes = len(content.encode("utf-8"))
        print(f"CACHE HIT: {cache_name} ({size_bytes:,} bytes)")
        return content

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"FETCH ERROR: Unable to reach {url} - {e}", file=sys.stderr)
        raise

    if response.status_code != 200:
        error_msg = f"FETCH FAILED: {url} returned status {response.status_code}"
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    content = response.text
    cache_path.write_text(content, encoding="utf-8")
    size_bytes = len(content.encode("utf-8"))
    print(f"FETCH: {url} -> saved to {cache_name} ({size_bytes:,} bytes)")
    return content

def main():
    print("--- Stage 1: Fetch once, cache once ---")
    html = fetch_page(START_URL, "catalogue-page-1.html")
    print(f"Page loaded successfully. Content length: {len(html):,} characters.")

if __name__ == "__main__":
    main()
