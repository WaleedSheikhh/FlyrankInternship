import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/WaleedSheikhh/FlyrankInternship)"
CACHE_DIR = "cache"
BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"

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
    time.sleep(0.5)  # politeness delay, only matters on real fetches
    return html


def discover_catalogue_pages():
    all_book_urls = set()
    current_url = BASE_CATALOGUE_URL
    page_num = 1
    MAX_PAGES = 3

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


if __name__ == "__main__":
    pages, book_urls = discover_catalogue_pages()
    print(f"catalogue_pages={pages}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(book_urls)}")