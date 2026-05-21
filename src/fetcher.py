from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class Fetcher:
    def __init__(self, timeout: float = 20.0) -> None:
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; ecom-scraper/1.0)"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    def get(self, url: str) -> str:
        return self.client.get(url).text

    def close(self) -> None:
        self.client.close()
