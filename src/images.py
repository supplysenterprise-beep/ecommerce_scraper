from __future__ import annotations

from pathlib import Path

import httpx
from slugify import slugify


def download_images(site: str, product_title: str, urls: list[str], out_dir: str) -> list[str]:
    target_dir = Path(out_dir) / site / slugify(product_title or "product")
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    with httpx.Client(timeout=30) as client:
        for idx, url in enumerate(urls):
            try:
                content = client.get(url).content
                path = target_dir / f"{idx}.jpg"
                path.write_bytes(content)
                saved.append(str(path))
            except Exception:
                continue
    return saved
