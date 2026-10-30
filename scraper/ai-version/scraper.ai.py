"""
QUARANTINED AI SCRAPER IMPLEMENTATION (Bonus Stage Benchmark)
Generated via prompt: 'Scrape the first 3 pages of books.toscrape.com and save 60 books into books.json with title and price.'
Noticeable flaws:
- No custom User-Agent (identifies as python-requests)
- No request timeout (vulnerable to infinite hangs)
- Zero rate limiting / delay (hammers the public server)
- No local disk caching (re-downloads everything on every run)
- Fragile extraction (.text on None crashes if description is missing)
- No Pydantic schema validation or type casting
"""

import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://books.toscrape.com/catalogue/"
books = []

for page in range(1, 4):
    url = f"{BASE_URL}page-{page}.html"
    res = requests.get(url)  # No timeout!
    soup = BeautifulSoup(res.text, "html.parser")
    
    for book in soup.select("article.product_pod"):
        title = book.h3.a["title"]
        price = book.select_one(".price_color").text
        book_url = urljoin(url, book.h3.a["href"])
        
        detail_res = requests.get(book_url)  # No politeness delay!
        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
        
        # Fragile: crashes if #product_description is absent
        desc_el = detail_soup.select_one("#product_description ~ p")
        desc = desc_el.text if desc_el else None
        
        books.append({
            "title": title,
            "price": price,
            "url": book_url,
            "desc": desc
        })

with open("books.json", "w", encoding="utf-8") as f:
    json.dump(books, f, indent=2)

print(f"Collected {len(books)} books.")
