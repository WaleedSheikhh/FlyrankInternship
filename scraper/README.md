# The Polite Scraper

A small, polite scraping pipeline that downloads the first three catalogue pages of [Books to Scrape](https://books.toscrape.com), visits all 60 book pages, and turns messy HTML into clean, validated JSON — without hammering the site or crashing on a broken page.

## Target classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Why:** A public sandbox built specifically for practicing web scraping — confirmed by reading toscrape.com directly.
- **Scope:** Only the first 3 catalogue pages, and the 60 book detail pages linked from them.
- **Data collected:** Book title, price, availability, rating, description, and source URL — all publicly shown on the page, nothing behind a login.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` — returned a 404. No robots file found. A missing file isn't permission on its own, but this site's own homepage explicitly states it exists for scraping practice, which is the actual permission here.

I will not reuse this code on another site without checking its rules and terms first.

## How to run it

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

Produces `output/books.json`, `output/errors.json`, and `output/run-report.json`.

## Record schema

Each record in `books.json`:

| Field | Type | Notes |
|---|---|---|
| title | string | |
| product_url | string | canonical identity — used to prevent duplicates |
| price_text | string | original text as shown on the page, e.g. "£17.27" |
| price_gbp | float | cleaned numeric price |
| availability_text | string | |
| rating_text | string or null | |
| description | string or null | null when the page has no description — never invented |
| source_page | string | which catalogue page this book was discovered from |
| fetched_at | string | UTC timestamp of when this record was collected |

## Politeness rules

- Every real request sends an honest `User-Agent` naming this project and linking to the repo.
- Every request has a 10-second timeout — never waits forever.
- A 0.5 second delay between real requests. Cached pages need no delay, since they never leave the machine.
- Every response's status code is checked before anything is parsed.
- Repeated runs read from `cache/` instead of re-requesting the site.

## Why this assignment needed no browser

The book data is already present in the HTML the server sends on first response — nothing here is loaded afterward by JavaScript. A real browser (like Playwright) would only add cost: slower runs, higher memory use, no extra data gained.

## Surviving failures

One deliberately broken URL is included in every run to prove the pipeline survives a bad page: it gets logged to `errors.json` with a reason, while the other 60 valid records are collected normally and the run still finishes.

## Sample run report

```json
{
  "start_time": "2026-09-02T12:14:49.542548+00:00",
  "duration_seconds": 1.527951,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1
}
```

## Ethics note

Use an official API when one exists, instead of scraping. Never bypass a login, a paywall, or an explicit block. Collect only the data actually needed for the task, and treat any real site's terms and `robots.txt` as the actual rule, not a suggestion — this project only touches a sandbox built for practice.

## Known limitation

This scraper is built specifically around Books to Scrape's current HTML structure. If the site's layout changes, the CSS selectors in `extract_book()` would need updating — this is not a general-purpose scraper for arbitrary sites.