from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser

from slugify import slugify

from src.browser import BrowserFetcher
from src.fetcher import Fetcher
from src.images import download_images
from src.storage import CrawlState, RawStore
from src.urls import normalize_url, same_domain


class Crawler:
    def __init__(self, site_key: str, site_cfg: dict, extractor, opts) -> None:
        self.site = site_key
        self.cfg = site_cfg
        self.extractor = extractor
        self.opts = opts
        self.fetcher = Fetcher(timeout=opts.timeout)
        self.browser = BrowserFetcher(headless=opts.headless) if (site_cfg.get("force_playwright") or site_cfg.get("playwright_fallback")) else None
        self.state = CrawlState("data/crawl_state.sqlite")
        self.store = RawStore("data/html")
        self.rows = []
        self.failed_path = Path("data/failed_urls.jsonl")
        self.robots = None
        if opts.respect_robots:
            self.robots = robotparser.RobotFileParser()
            self.robots.set_url(normalize_url(site_cfg["start_url"], "/robots.txt"))
            self.robots.read()

    def allowed(self, url: str) -> bool:
        return same_domain(url, self.cfg["allowed_domains"]) and (not self.robots or self.robots.can_fetch("*", url))

    def fetch(self, url: str, for_listing: bool = False) -> str:
        html = ""
        if self.cfg.get("static_first", True) and not self.cfg.get("force_playwright"):
            html = self.fetcher.get(url)
        if (not html or "enable javascript" in html.lower() or "please enable" in html.lower()) and self.browser:
            html = self.browser.get_with_scroll(url) if for_listing else self.browser.get(url)
        return html

    def run(self):
        self.state.add_pending(self.cfg["start_url"], "category")
        pages = products = 0
        while True:
            item = self.state.pop_pending()
            if not item:
                break
            url, kind = item
            if self.opts.max_pages and pages >= self.opts.max_pages:
                break
            if not self.allowed(url):
                continue
            try:
                html = self.fetch(url, for_listing=(kind == "category"))
                html_path = self.store.save_html(self.site, slugify(url)[:120], html)
                pages += 1
                cats = [normalize_url(url, x) for x in self.extractor.category_links(html, url)]
                prods = [normalize_url(url, x) for x in self.extractor.product_links(html, url)]
                nexts = [normalize_url(url, x) for x in self.extractor.next_pages(html, url)]
                for c in cats + nexts:
                    if self.allowed(c):
                        self.state.add_pending(c, "category")
                for p in prods:
                    if self.allowed(p):
                        self.state.add_pending(p, "product")
                if kind == "product" and not self.opts.dry_run:
                    data = self.extractor.product_data(html, url)
                    row = {
                        "site": self.site,
                        "brand": self.site,
                        "category_path": data.get("category_path", []),
                        "category_url": "",
                        "product_url": url,
                        "title": data.get("title", ""),
                        "sku": data.get("sku", ""),
                        "model": data.get("model", ""),
                        "description_html": data.get("description_html", ""),
                        "description_text": data.get("description_text", ""),
                        "features": data.get("features", []),
                        "specifications": data.get("specifications", {}),
                        "image_urls": data.get("image_urls", []),
                        "image_paths": [],
                        "raw_html_path": html_path,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if self.opts.download_images:
                        row["image_paths"] = download_images(self.site, row["title"], row["image_urls"], "data/images")
                    self.rows.append(row)
                    products += 1
                    if self.opts.max_products and products >= self.opts.max_products:
                        break
                self.state.mark_visited(url, kind)
                if self.opts.delay:
                    time.sleep(self.opts.delay)
                print(json.dumps({"site": self.site, "url": url, "kind": kind, "categories": len(cats), "products": len(prods)}))
            except Exception as e:
                self.state.mark_failed(url, str(e))
                self.failed_path.parent.mkdir(parents=True, exist_ok=True)
                with self.failed_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"site": self.site, "url": url, "error": str(e)}) + "\n")
        return self.rows

    def close(self):
        self.fetcher.close()
        if self.browser:
            self.browser.close()
