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
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if not match:
        raise ValueError(f"No numeric price found in: {price_text}")
    return float(match.group(1))

def fetch_page(url: str, cache_name: str, telemetry: dict, allow_retry: bool = True) -> tuple[str, bool]:
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        content = cache_path.read_text(encoding="utf-8")
        telemetry["cache_hits"] += 1
        return content, True

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    def _attempt_request():
        telemetry["pages_fetched"] += 1
        return requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

    try:
        response = _attempt_request()
    except (requests.Timeout, requests.ConnectionError) as e:
        if allow_retry:
            print(f"[RETRY] Network issue on {url} ({e}). Retrying once after 1s...")
            time.sleep(1.0)
            response = _attempt_request()
        else:
            raise

    # Do not retry client rejections (404 / 403)
    if response.status_code in (403, 404):
        error_msg = f"Client error {response.status_code} for {url} - skipping without retry"
        print(f"[HTTP {response.status_code}] {error_msg}", file=sys.stderr)
        raise RuntimeError(error_msg)

    # Server errors (5xx) get one retry if allowed
    if response.status_code >= 500:
        if allow_retry:
            print(f"[RETRY] Server error {response.status_code} on {url}. Retrying once after 1s...")
            time.sleep(1.0)
            response = _attempt_request()
        if response.status_code >= 500:
            error_msg = f"Persistent server error {response.status_code} on {url}"
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg)

    if response.status_code != 200:
        error_msg = f"Unexpected status {response.status_code} on {url}"
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    content = response.text
    cache_path.write_text(content, encoding="utf-8")
    return content, False

def discover_book_items(max_pages: int, telemetry: dict) -> list[dict]:
    current_url = START_URL
    pages_crawled = 0
    discovered_items: list[dict] = []
    seen_urls: set[str] = set()

    while current_url and pages_crawled < max_pages:
        pages_crawled += 1
        cache_file = f"catalogue-page-{pages_crawled}.html"
        html_content, from_cache = fetch_page(current_url, cache_file, telemetry=telemetry, allow_retry=True)

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

def run_pipeline(max_pages: int = 3, inject_fake_url: bool = True) -> tuple[list[dict], list[dict], dict]:
    start_time = datetime.now(timezone.utc)
    telemetry = {
        "pages_fetched": 0,
        "cache_hits": 0,
        "failed_pages": 0
    }

    items = discover_book_items(max_pages=max_pages, telemetry=telemetry)

    # Stage 5 requirement: inject one made-up broken URL to prove failure survival
    if inject_fake_url:
        items.append({
            "product_url": "https://books.toscrape.com/catalogue/fake-broken-book_9999/index.html",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html"
        })

    valid_records: list[dict] = []
    error_records: list[dict] = []
    seen_canonical_urls: set[str] = set()

    for idx, item in enumerate(items, start=1):
        url = item["product_url"]
        path_parts = [p for p in urlparse(url).path.split("/") if p and p != "index.html"]
        slug = path_parts[-1] if path_parts else f"book-{idx}"
        cache_name = f"book-{slug}.html"

        # Handle each page separately: single-page failure does not abort the run
        try:
            html, from_cache = fetch_page(url, cache_name, telemetry=telemetry, allow_retry=True)
            if not from_cache:
                time.sleep(POLITE_DELAY)

            raw_record = parse_book_detail(html, product_url=url, source_page=item["source_page"])
            raw_record["price_gbp"] = clean_price_gbp(raw_record["price_text"])

            validated = BookRecord(**raw_record)
            rec_dict = validated.model_dump()

            if rec_dict["product_url"] not in seen_canonical_urls:
                seen_canonical_urls.add(rec_dict["product_url"])
                valid_records.append(rec_dict)

        except Exception as exc:
            telemetry["failed_pages"] += 1
            print(f"[SURVIVED] Skipped failed page: {url} -> {exc}")
            error_records.append({
                "product_url": url,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            })

    end_time = datetime.now(timezone.utc)
    duration_seconds = round((end_time - start_time).total_seconds(), 2)

    # Persist data outputs
    books_file = OUTPUT_DIR / "books.json"
    errors_file = OUTPUT_DIR / "errors.json"
    report_file = OUTPUT_DIR / "run-report.json"

    books_file.write_text(json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8")
    errors_file.write_text(json.dumps(error_records, indent=2, ensure_ascii=False), encoding="utf-8")

    run_report = {
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration_seconds,
        "pages_fetched": telemetry["pages_fetched"],
        "cache_hits": telemetry["cache_hits"],
        "valid_records": len(valid_records),
        "invalid_records": len(error_records) - telemetry["failed_pages"],
        "failed_pages": telemetry["failed_pages"]
    }

    report_file.write_text(json.dumps(run_report, indent=2, ensure_ascii=False), encoding="utf-8")
    return valid_records, error_records, run_report

def main():
    print("--- Stage 5: Survive failures, report the run ---")
    valid, errors, report = run_pipeline(max_pages=3, inject_fake_url=True)
    print("\nRun Report (run-report.json):")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
