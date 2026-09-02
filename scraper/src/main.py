import requests
import os
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from datetime import datetime, timezone

import sys
sys.stdout.reconfigure(encoding="utf-8")

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/WaleedSheikhh/FlyrankInternship)"
CACHE_DIR = "cache"
BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_PAGES = 3


import re
import json
from pydantic import BaseModel, ValidationError
from typing import Optional


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str]
    description: Optional[str]
    source_page: str
    fetched_at: str


def clean_price(price_text):
    # strip everything except digits and the decimal point — avoids the £ encoding issue entirely
    cleaned = re.sub(r"[^\d.]", "", price_text)
    return float(cleaned)


def fetch_page(url, cache_filename):
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")

    html = response.text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    time.sleep(0.5)
    return html


def discover_catalogue_pages():
    all_book_urls = set()
    current_url = BASE_CATALOGUE_URL
    page_num = 1

    while current_url and page_num <= MAX_PAGES:
        cache_filename = f"catalogue-page-{page_num}.html"
        html = fetch_page(current_url, cache_filename)
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            book_url = urljoin(current_url, link["href"])
            all_book_urls.add(book_url)

        next_link = soup.select_one("li.next a")
        if next_link and page_num < MAX_PAGES:
            current_url = urljoin(current_url, next_link["href"])
            page_num += 1
        else:
            current_url = None

    return page_num, all_book_urls


def extract_book(url, source_page):
    # cache filename from the book's own URL, so each book gets its own file
    safe_name = url.rstrip("/").split("/")[-2] + ".html"
    html = fetch_page(url, safe_name)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")
    title = product_main.select_one("h1").get_text(strip=True)
    price_text = product_main.select_one("p.price_color").get_text(strip=True)
    availability_text = product_main.select_one("p.availability").get_text(strip=True)

    rating_tag = product_main.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    run_start = datetime.now(timezone.utc)

    pages, book_urls = discover_catalogue_pages()
    print(f"catalogue_pages={pages}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(book_urls)}")

    # deliberately broken URL, added on purpose to prove failure survival
    book_urls_list = list(book_urls) + ["https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"]

    valid_records = []
    invalid_records = []
    seen_urls = set()
    cache_hits = 0
    fetches = 0
    failed_pages = 0

    for i, url in enumerate(book_urls_list, 1):
        try:
            cache_path_check = os.path.join(CACHE_DIR, url.rstrip("/").split("/")[-2] + ".html")
            was_cached = os.path.exists(cache_path_check)

            raw = extract_book(url, BASE_CATALOGUE_URL)

            if was_cached:
                cache_hits += 1
            else:
                fetches += 1

            if raw["product_url"] in seen_urls:
                continue
            seen_urls.add(raw["product_url"])

            raw["price_gbp"] = clean_price(raw["price_text"])
            book = Book(**raw)
            valid_records.append(book.model_dump())
            print(f"[{i}/{len(book_urls_list)}] OK: {book.title}")

        except Exception as e:
            failed_pages += 1
            invalid_records.append({"url": url, "reason": str(e)})
            print(f"[{i}/{len(book_urls_list)}] FAILED: {url} — {e}")

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    run_end = datetime.now(timezone.utc)
    report = {
        "start_time": run_start.isoformat(),
        "duration_seconds": (run_end - run_start).total_seconds(),
        "pages_fetched": fetches,
        "cache_hits": cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": failed_pages
    }
    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")
    print(f"failed_pages={failed_pages}")
    pages, book_urls = discover_catalogue_pages()
    print(f"catalogue_pages={pages}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(book_urls)}")

    valid_records = []
    invalid_records = []
    seen_urls = set()

    book_urls_list = list(book_urls)
    for i, url in enumerate(book_urls_list, 1):
        try:
            raw = extract_book(url, BASE_CATALOGUE_URL)

            # canonical URL — skip if we've already stored this one
            if raw["product_url"] in seen_urls:
                continue
            seen_urls.add(raw["product_url"])

            raw["price_gbp"] = clean_price(raw["price_text"])

            book = Book(**raw)
            valid_records.append(book.model_dump())
            print(f"[{i}/{len(book_urls_list)}] OK: {book.title}")

        except (ValidationError, Exception) as e:
            invalid_records.append({"url": url, "reason": str(e)})
            print(f"[{i}/{len(book_urls_list)}] INVALID: {url} — {e}")

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")