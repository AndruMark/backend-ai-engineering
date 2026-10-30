# Polite Web Scraper (BE-05 / W5-A9)

A respectful, fault-tolerant web scraping and data ingestion pipeline built with Python, Requests, BeautifulSoup4, and Pydantic. It extracts book records from the Books to Scrape sandbox, normalizes text into typed schemas, enforces Pydantic validation, survives broken pages, and generates runtime execution reports.

---

## 1. Target Classification & Ethics
- **Target Site**: `https://books.toscrape.com/`
- **Purpose**: Public practice sandbox built specifically for practicing web crawling, DOM extraction, and ingestion pipelines without operational impact.
- **Scope**: Exactly the first 3 catalogue pages (`catalogue/page-1.html` through `catalogue/page-3.html`), discovering and extracting 60 individual book records.
- **Data Collected**: Title, canonical product URL, raw price text, normalized price in GBP, availability, star rating, description, source catalogue page, and fetch timestamp.
- **robots.txt Assessment**: Queried `https://books.toscrape.com/robots.txt` returning `HTTP 404 Not Found` (no robots exclusion file declared). A missing file is not blanket permission; data collection is strictly bounded to the explicitly provisioned practice sandbox.
- **Ethical Scraper Statement**: "I will not reuse this code on another site without checking its rules and terms first."
- **Ethics Note**: Always use an official API when one exists; never bypass authentication, paywalls, or rate limiters; and collect only the minimum necessary data.

---

## 2. Quickstart & One-Command Run
Clone the repository and run the pipeline:

```powershell
# 1. Navigate to scraper folder
cd scraper

# 2. Install dependencies
pip install -r ../requirements.txt

# 3. Execute the pipeline
python src/main.py
3. Politeness Architecture
User-Agent Identification: Every request sends FlyRankInternship-A9/1.0 (+https://github.com/AndruMark/backend-ai-engineering) identifying the client and repository.

Network Timeout: Strict 10-second timeout threshold on outbound calls (timeout=10).

Throttled Delay: Minimum 500 ms pause between live network calls (POLITE_DELAY = 0.5).

Local Disk Cache: Saves raw HTML responses to cache/ (catalogue-page-*.html and book-*.html). Subsequent runs read from disk in 0 ms without issuing external HTTP requests.

No Headless Browser Overhead: Since the target server renders static HTML containing all required fields directly in the initial HTTP payload, a headless browser (Playwright/Puppeteer) would only introduce unnecessary memory, CPU, and latency overhead without providing any extraction benefit.

4. Record Schema & Data Contracts
Records are validated against a strict Pydantic model before storage:

Python
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
Clean Output: Valid records are stored in output/books.json.

Idempotency Guarantee: Running the scraper multiple times produces the exact same 60 records—never duplicating to 120.

Quarantine: Malformed or failing records are isolated in output/errors.json.

5. Fault Tolerance & Run Report Telemetry
Client errors (404 / 403) are logged and skipped immediately without retrying.

Server errors (5xx) and connection timeouts retry once after a 1-second backoff.

In Stage 5, a simulated broken URL (https://books.toscrape.com/catalogue/fake-broken-book_9999/index.html) was injected into the queue: the scraper logged and skipped the failure, preserved the 60 valid records, and recorded the failure in telemetry.

Execution Evidence (output/run-report.json):
JSON
{
  "start_time": "2026-10-30T19:49:13Z",
  "duration_seconds": 1.05,
  "pages_fetched": 1,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
6. Honest Limitations
Pagination Limit: The crawler currently relies on following pagination sequentially up to max_pages=3 rather than dynamic breadth-first crawling across the entire catalogue.

Fixed Selectors: Selectors assume the current DOM layout of books.toscrape.com; breaking markup changes would require selector updates.

---

## 7. Bonus Stage: AI vs Me (Rematch Benchmark)

### Prompt Provided to the Autonomous AI
> "Build a Python web scraper for books.toscrape.com that collects all 60 books across the first three catalogue pages and writes them to books.json with their title, canonical URL, raw price, numeric price in GBP, availability, rating, and description. Implement local disk caching, an honest User-Agent, at least 500ms delay between live requests, 10s timeouts, Pydantic schema validation, quarantine for malformed records in errors.json, fault tolerance that retries 5xx/timeouts but skips 404s without crashing, and a final run-report.json telemetry summary."

### Comparative Analysis & 3 Concrete Architectural Discrepancies
Comparing the quarantined autonomous implementation in `scraper/ai-version/scraper.ai.py` against the production pipeline in `scraper/src/main.py` revealed three major vulnerabilities:

1. **Zero Throttling & Server Hammering (Politeness Violation)**: The AI script executed 60 detail requests in rapid back-to-back succession without `time.sleep()`. On production servers or protected endpoints, this triggers immediate IP rate-limiting, WAF blocks, or 429 Too Many Requests responses. The production pipeline guarantees at least 500 ms delay between real network requests.
2. **Missing Local Disk Cache Architecture**: The AI version lacked any disk caching mechanism, re-fetching all catalogue and detail pages on every single run. The production implementation uses `cache/` (`catalogue-page-*.html` and `book-*.html`), enabling sub-second idempotent re-runs and saving server bandwidth.
3. **Fragile DOM Extraction & Schema Absence**: The AI version did not use Pydantic or schema validation. It extracted raw string tuples and risked `AttributeError` crashes on missing description tags. The production pipeline normalizes currency strings (`£51.77` -> `51.77`), validates data types via Pydantic (`BookRecord`), isolates failing rows to `errors.json`, and records full data provenance (`source_page` and `fetched_at`).
