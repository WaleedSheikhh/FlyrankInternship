## Target classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Why:** It's a public sandbox built specifically for practicing web scraping — confirmed by reading toscrape.com directly.
- **Scope:** Only the first 3 catalogue pages, and the ~60 book detail pages linked from them.
- **Data collected:** Book title, price, availability, rating, description, and source URL — all publicly shown on the page, nothing behind a login.
- **robots.txt result:** Requested https://books.toscrape.com/robots.txt — returned a 404. No robots file found. A missing file isn't permission on its own, but this site's own homepage explicitly states it exists for scraping practice, which is the actual permission here.

I will not reuse this code on another site without checking its rules and terms first.