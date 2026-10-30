# Polite Web Scraper (BE-05)

A respectful, fault-tolerant web scraping and data ingestion pipeline that extracts book records from the Books to Scrape sandbox, normalizes text into typed schemas, enforces Pydantic validation, and generates runtime execution reports.

## Target Classification
- **Target Site**: https://books.toscrape.com/
- **Site Purpose**: Dedicated sandbox platform explicitly built for practicing web scraping, crawling, and parsing techniques.
- **Scope**: The first 3 catalogue pages (`catalogue/page-1.html` through `catalogue/page-3.html`), discovering and extracting exactly 60 individual book records.
- **Data Collected**: Book title, canonical product URL, raw price text, normalized GBP price, availability status, star rating, product description, and provenance metadata (source page and fetch timestamp).
- **robots.txt Assessment**: Queried `https://books.toscrape.com/robots.txt` returning `404 Not Found` (no robots exclusion file declared).
- **Ethical Scraper Statement**: "I will not reuse this code on another site without checking its rules and terms first."

## Politeness Protocol
1. **User-Agent**: `FlyRankInternship-A9/1.0 (+https://github.com/AndruMark/backend-ai-engineering)` identifying the client and source code repository.
2. **Network Timeout**: 10-second timeout threshold on all outbound HTTP calls.
3. **Throttling**: Minimum 500 ms delay between real network requests.
4. **Local Disk Cache**: Saves all fetched HTML pages to `cache/` to ensure development runs do not hit the public server repeatedly.
5. **No Headless Browser Overhead**: Since the server sends static HTML containing all required fields directly in the response payload, raw HTTP requests are used instead of browser automation (Playwright/Puppeteer), avoiding unnecessary CPU and memory consumption.
