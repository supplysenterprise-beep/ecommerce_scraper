from __future__ import annotations

import json
import re
from bs4 import BeautifulSoup

from src.extractors.base import BaseExtractor


class GenericExtractor(BaseExtractor):
    cat_re = re.compile(r"/(product-category|category|products|tools)/", re.I)
    prod_re = re.compile(r"/(product|products)/", re.I)

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def category_links(self, html: str, url: str) -> list[str]:
        soup = self._soup(html)
        return [a.get("href") for a in soup.select("a[href]") if self.cat_re.search(a.get("href", ""))]

    def product_links(self, html: str, url: str) -> list[str]:
        soup = self._soup(html)
        return [a.get("href") for a in soup.select("a[href]") if self.prod_re.search(a.get("href", "")) and "category" not in a.get("href", "")]

    def next_pages(self, html: str, url: str) -> list[str]:
        soup = self._soup(html)
        links = []
        for a in soup.select("a.next, a[rel='next'], .pagination a, a"):
            h = a.get("href", "")
            if "page" in h or "paged" in h or "next" in (a.get_text() or "").lower():
                links.append(h)
        return links

    def product_data(self, html: str, url: str) -> dict:
        soup = self._soup(html)
        title = (soup.select_one("h1") or soup.select_one("meta[property='og:title']"))
        title_text = title.get_text(strip=True) if title and title.name != "meta" else (title.get("content", "") if title else "")
        desc_node = soup.select_one(".description, .product-description, [itemprop='description'], .entry-content")
        desc_html = str(desc_node) if desc_node else ""
        desc_text = desc_node.get_text(" ", strip=True) if desc_node else ""
        features = [li.get_text(" ", strip=True) for li in soup.select("ul li") if li.get_text(strip=True)]
        specs = {}
        for row in soup.select("table tr"):
            cells = row.select("th,td")
            if len(cells) >= 2:
                specs[cells[0].get_text(" ", strip=True)] = cells[1].get_text(" ", strip=True)
        images = []
        for img in soup.select("img"):
            for attr in ("src", "data-src", "srcset"):
                v = img.get(attr)
                if v:
                    images.append(v.split(" ")[0])
        breadcrumbs = [x.get_text(" ", strip=True) for x in soup.select(".breadcrumb li, nav[aria-label='breadcrumb'] li") if x.get_text(strip=True)]
        sku = ""
        text = soup.get_text("\n", strip=True)
        m = re.search(r"(SKU|Model|Order\s*Number)\s*[:#]?\s*([A-Z0-9\-_/]+)", text, re.I)
        if m:
            sku = m.group(2)
        for s in soup.select("script[type='application/ld+json']"):
            try:
                data = json.loads(s.get_text(strip=True))
                if isinstance(data, dict) and data.get("@type") == "Product":
                    title_text = title_text or data.get("name", "")
                    sku = sku or data.get("sku", "")
            except Exception:
                pass
        return {
            "title": title_text,
            "sku": sku,
            "model": sku,
            "description_html": desc_html,
            "description_text": desc_text,
            "features": features[:100],
            "specifications": specs,
            "image_urls": list(dict.fromkeys(images)),
            "category_path": breadcrumbs,
        }
