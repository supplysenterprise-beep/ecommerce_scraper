from __future__ import annotations

import re
from src.extractors.generic import GenericExtractor


class Extractor(GenericExtractor):
    def category_links(self, html: str, url: str) -> list[str]:
        links = super().category_links(html, url)
        return [u for u in links if re.search(r"(product-category|/products|product\?cid=|professional|tools|catalog)", u, re.I)]

    def product_links(self, html: str, url: str) -> list[str]:
        links = super().product_links(html, url)
        return [u for u in links if re.search(r"(/product/|/product/detail/|/en-us/products/)", u, re.I)]
