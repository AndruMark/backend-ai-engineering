import os
import sys
import time
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from typing import Optional
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

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

class BookRecord(BaseModel):
    """
    Strict validation schema for normalized book records.
    """
    title: str = Field(min_length=1)
    product_url: str
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0.0)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_absolute_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL must be absolute and use HTTPS: {v}")
        return v

def clean_price_gbp(price_text: str) -> float:
    """
    Extracts numeric float from messy currency strings (e.g. '£51.77' or 'Â£51.77').
    """
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if not match:
        raise ValueError(f"No numeric price found in: {price_text}")
    return float(match.group(1))

def fetch_page(url: str, cache_name: str) -> tuple[str, bool]:
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

    return discovered_items

def parse_book_detail(html_content: str, product_url: str, source_page: str) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")
    product_article = soup.select_one("article.product_page")
    if not product_article:
        raise ValueError(f"Product page container not found for {product_url}")

    title_tag = product_article.select_one("div.product_main h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    price_tag = product_article.select_one("div.product_main p.price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else ""

    avail_tag = product_article.select_one("div.product_main p.instock.availability")
    availability_text = " ".join(avail_tag.get_text().split()) if avail_tag else ""

    rating_tag = product_article.select_one("p.star-rating")
    rating_text = "Zero"
    if rating_tag:
        for c in rating_tag.get("class", []):
            if c != "star-rating":
                rating_text = c
                break

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

def process_pipeline(max_pages: int = 3) -> tuple[list[dict], list[dict]]:
    items = discover_book_items(max_pages=max_pages)
    valid_records: list[dict] = []
    error_records: list[dict] = []
    seen_canonical_urls: set[str] = set()
    total = len(items)

    for idx, item in enumerate(items, start=1):
        url = item["product_url"]
        path_parts = [p for p in urlparse(url).path.split("/") if p and p != "index.html"]
        slug = path_parts[-1] if path_parts else f"book-{idx}"
        cache_name = f"book-{slug}.html"

        html, from_cache = fetch_page(url, cache_name)
        if not from_cache:
            time.sleep(POLITE_DELAY)

        try:
            raw_record = parse_book_detail(html, product_url=url, source_page=item["source_page"])
            
            # Normalization
            raw_record["price_gbp"] = clean_price_gbp(raw_record["price_text"])

            # Schema Validation
            validated = BookRecord(**raw_record)
            record_dict = validated.model_dump()

            # Canonical deduplication
            if record_dict["product_url"] not in seen_canonical_urls:
                seen_canonical_urls.add(record_dict["product_url"])
                valid_records.append(record_dict)

        except Exception as exc:
            error_records.append({
                "product_url": url,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            })

    # Save outputs idempotently
    books_file = OUTPUT_DIR / "books.json"
    errors_file = OUTPUT_DIR / "errors.json"

    books_file.write_text(json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8")
    errors_file.write_text(json.dumps(error_records, indent=2, ensure_ascii=False), encoding="utf-8")

    return valid_records, error_records

def main():
    print("--- Stage 4: Clean it, check it, store it ---")
    valid, errors = process_pipeline(max_pages=3)
    print(f"Validated records stored: {len(valid)}")
    print(f"Rejected records stored: {len(errors)}")

if __name__ == "__main__":
    main()
