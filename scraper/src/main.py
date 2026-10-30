import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Base configuration & Politeness headers
BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/AndruMark/backend-ai-engineering)"
REQUEST_TIMEOUT = 10   # seconds
POLITE_DELAY = 0.5     # minimum 500ms between real network calls

# Resolve directories relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_page(url: str, cache_name: str) -> tuple[str, bool]:
    """
    Polite fetcher with local disk cache:
    Returns (html_content, from_cache: bool).
    """
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        content = cache_path.read_text(encoding="utf-8")
        size_bytes = len(content.encode("utf-8"))
        print(f"CACHE HIT: {cache_name} ({size_bytes:,} bytes)")
        return content, True

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
    return content, False

def discover_book_urls(max_pages: int = 3) -> list[str]:
    """
    Crawls catalogue pages sequentially following 'next' links,
    normalizing relative product links to absolute URLs and removing duplicates.
    """
    current_url = START_URL
    pages_crawled = 0
    all_book_urls: list[str] = []

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        cache_file = f"catalogue-page-{pages_crawled}.html"
        html_content, from_cache = fetch_page(current_url, cache_file)

        # Politeness rule: sleep only if a live network request occurred
        if not from_cache:
            time.sleep(POLITE_DELAY)

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract book links from product pods
        product_links = soup.select("article.product_pod h3 a")
        for link in product_links:
            href = link.get("href")
            if href:
                abs_url = urljoin(current_url, href)
                all_book_urls.append(abs_url)

        # Follow pagination link
        next_tag = soup.select_one("li.next a")
        if next_tag and next_tag.get("href"):
            current_url = urljoin(current_url, next_tag.get("href"))
        else:
            current_url = None

    # Deduplicate preserving discovery order
    unique_urls = list(dict.fromkeys(all_book_urls))
    print(f"catalogue_pages = {pages_crawled}, discovered = {len(all_book_urls)}, unique_urls = {len(unique_urls)}")
    return unique_urls

def main():
    print("--- Stage 2: Discover three catalogue pages ---")
    urls = discover_book_urls(max_pages=3)
    print(f"Sample book URL: {urls[0] if urls else 'None'}")

if __name__ == "__main__":
    main()
