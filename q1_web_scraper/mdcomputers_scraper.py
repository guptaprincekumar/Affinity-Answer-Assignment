#!/usr/bin/env python3
"""Scrape product listings from mdcomputers.in for a given search term.

The site sits behind Cloudflare bot protection which rejects the default
Python TLS fingerprint (plain `requests` gets a 403), so the page is fetched
with `curl_cffi`, which performs the request with a real-browser TLS handshake.

Usage:
    python mdcomputers_scraper.py "external hard drive"
    python mdcomputers_scraper.py "ssd" --pages 3 --output ssd.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys

from bs4 import BeautifulSoup
from curl_cffi import requests

BASE_URL = "https://mdcomputers.in/index.php"
REQUEST_TIMEOUT_SECONDS = 30

CSV_COLUMNS = ["name", "price_inr", "mrp_inr", "discount_label", "product_url"]


def fetch_search_page(search_term: str, page: int) -> str:
    """Fetch one search-results page and return its HTML.

    Raises:
        RuntimeError: If the site does not respond with HTTP 200.
    """
    params = {"route": "product/search", "search": search_term}
    if page > 1:
        params["page"] = page
    response = requests.get(
        BASE_URL,
        params=params,
        impersonate="chrome",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Search request failed with HTTP {response.status_code} "
            f"for term '{search_term}' (page {page})"
        )
    return response.text


def parse_products(html: str) -> list[dict]:
    """Extract product rows from a search-results page."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for card in soup.select("div.product-grid-item"):
        title_link = card.select_one("h3.product-entities-title a")
        if title_link is None:
            continue
        products.append(
            {
                "name": title_link.get_text(strip=True),
                "price_inr": _parse_amount(_price_text(card, "span.ins")),
                "mrp_inr": _parse_amount(_price_text(card, "span.del")),
                "discount_label": _discount_label(card),
                "product_url": title_link.get("href", ""),
            }
        )
    return products


def total_pages(html: str) -> int:
    """Read the page count from the "Showing 1 to 18 of 54 (3 Pages)" footer."""
    match = re.search(r"\((\d+)\s+Pages?\)", html)
    return int(match.group(1)) if match else 1


def scrape(search_term: str, max_pages: int) -> list[dict]:
    """Scrape up to `max_pages` result pages for `search_term`."""
    first_page_html = fetch_search_page(search_term, page=1)
    products = parse_products(first_page_html)
    pages_to_fetch = min(max_pages, total_pages(first_page_html))
    for page in range(2, pages_to_fetch + 1):
        products.extend(parse_products(fetch_search_page(search_term, page)))
    return products


def write_csv(products: list[dict], output) -> None:
    """Write products as CSV to an open file handle."""
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(products)


def _price_text(card, selector: str) -> str:
    """Return the text of a price node inside a product card, or ''."""
    node = card.select_one(f"span.price {selector}")
    if node is None:
        # Products without a discount carry a single .amount node.
        node = card.select_one("span.price span.amount") if selector == "span.ins" else None
    return node.get_text(strip=True) if node else ""


def _parse_amount(text: str) -> str:
    """Turn '₹9,140' into '9140'; return '' when there is no price."""
    digits = re.sub(r"[^\d]", "", text)
    return digits


def _discount_label(card) -> str:
    """Return the sale label (e.g. '-9%') shown on the card, or ''."""
    label = card.select_one("span.onsale.product-label")
    return label.get_text(strip=True) if label else ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract product listings from mdcomputers.in for a search term."
    )
    parser.add_argument("search_term", help="term to search for, e.g. 'external hard drive'")
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="maximum number of result pages to fetch (default: 1)",
    )
    parser.add_argument(
        "--output",
        help="write CSV to this file instead of stdout",
    )
    args = parser.parse_args()

    try:
        products = scrape(args.search_term, max_pages=args.pages)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not products:
        print(f"No products found for '{args.search_term}'.", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as handle:
            write_csv(products, handle)
        print(f"Wrote {len(products)} products to {args.output}", file=sys.stderr)
    else:
        write_csv(products, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
