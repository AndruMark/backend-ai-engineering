import os
import sys
import time
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
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
    return content, False

def discover_book_items(max_pages: int = 3) -> list[dict]:
    current_url = START_URL
    pages_crawled = 0
    discovered_items: list[dict] = []
    seen_urls: set[str] = set()

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        cache_file = f"catalogue-page-{pages_crawled}.html"
        html_content, from_cache = fetch_page(current_url, cache_file)

        if not from_cache:
            time.sleep(POLITE_DELAY)

        soup = BeautifulSoup(html_content, "html.parser")

        product_links = soup.select("article.product_pod h3 a")
        for link in product_links:
            href = link.get("href")
            if href:
                abs_url = urljoin(current_url, href)
                if abs_url not in seen_urls:
                    seen_urls.add(abs_url)
                    discovered_items.append({
                        "product_url": abs_url,
                        "source_page": current_url
                    })

        next_tag = soup.select_one("li.next a")
        if next_tag and next_tag.get("href"):
            current_url = urljoin(current_url, next_tag.get("href"))
        else:
            current_url = None

    print(f"catalogue_pages = {pages_crawled}, discovered = {len(discovered_items)}, unique_urls = {len(seen_urls)}")
    return discovered_items

def parse_book_detail(html_content: str, product_url: str, source_page: str) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")
    product_article = soup.select_one("article.product_page")
    if not product_article:
        raise ValueError(f"Product page container not found for {product_url}")

    # 1. Title
    title_tag = product_article.select_one("div.product_main h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # 2. Raw price
    price_tag = product_article.select_one("div.product_main p.price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else ""

    # 3. Raw availability
    avail_tag = product_article.select_one("div.product_main p.instock.availability")
    availability_text = " ".join(avail_tag.get_text().split()) if avail_tag else ""

    # 4. Rating text
    rating_tag = product_article.select_one("p.star-rating")
    rating_text = "Zero"
    if rating_tag:
        classes = rating_tag.get("class", [])
        for c in classes:
            if c != "star-rating":
                rating_text = c
                break

    # 5. Description (null if missing)
    desc_header = product_article.select_one("#product_description")
    description = None
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            desc_text = desc_p.get_text(strip=True)
            description = desc_text if desc_text else None

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }

def extract_all_books(max_pages: int = 3) -> list[dict]:
    items = discover_book_items(max_pages=max_pages)
    raw_records: list[dict] = []
    total = len(items)

    for idx, item in enumerate(items, start=1):
        url = item["product_url"]
        path_parts = [p for p in urlparse(url).path.split("/") if p and p != "index.html"]
        slug = path_parts[-1] if path_parts else f"book-{idx}"
        cache_name = f"book-{slug}.html"

        html, from_cache = fetch_page(url, cache_name)
        status_label = "CACHE" if from_cache else "FETCH"
        print(f"[{idx:02d}/{total:02d}] {status_label}: {slug}")

        if not from_cache:
            time.sleep(POLITE_DELAY)

        record = parse_book_detail(html, product_url=url, source_page=item["source_page"])
        raw_records.append(record)

    return raw_records

def main():
    print("--- Stage 3: Extract book details ---")
    records = extract_all_books(max_pages=3)
    print(f"\ndetail_pages = {len(records)}")
    if records:
        print("\nSample raw record (all 8 keys):")
        print(json.dumps(records[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
