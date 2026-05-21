from __future__ import annotations

from playwright.sync_api import sync_playwright


class BrowserFetcher:
    def __init__(self, headless: bool = True, timeout_ms: int = 30000) -> None:
        self._p = sync_playwright().start()
        self.browser = self._p.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        self.timeout_ms = timeout_ms

    def get(self, url: str) -> str:
        self.page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)
        return self.page.content()

    def get_with_scroll(self, url: str, rounds: int = 4) -> str:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        for _ in range(rounds):
            self.page.mouse.wheel(0, 5000)
            self.page.wait_for_timeout(800)
        return self.page.content()

    def close(self) -> None:
        self.browser.close()
        self._p.stop()
