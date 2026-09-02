import requests
import os

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/WaleedSheikhh/FlyrankInternship)"
CACHE_DIR = "cache"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"

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
    return html

if __name__ == "__main__":
    fetch_page(CATALOGUE_URL, "catalogue-page-1.html")