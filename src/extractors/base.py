from __future__ import annotations

from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    @abstractmethod
    def category_links(self, html: str, url: str) -> list[str]: ...

    @abstractmethod
    def product_links(self, html: str, url: str) -> list[str]: ...

    @abstractmethod
    def next_pages(self, html: str, url: str) -> list[str]: ...

    @abstractmethod
    def product_data(self, html: str, url: str) -> dict: ...
