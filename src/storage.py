from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class CrawlState:
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init()

    def _init(self) -> None:
        c = self.conn.cursor()
        c.execute("create table if not exists pending(url text primary key, kind text)")
        c.execute("create table if not exists visited(url text primary key, kind text)")
        c.execute("create table if not exists failed(url text primary key, error text)")
        self.conn.commit()

    def add_pending(self, url: str, kind: str) -> None:
        self.conn.execute("insert or ignore into pending(url,kind) values(?,?)", (url, kind))
        self.conn.commit()

    def pop_pending(self):
        row = self.conn.execute("select url,kind from pending limit 1").fetchone()
        if not row:
            return None
        self.conn.execute("delete from pending where url=?", (row[0],))
        self.conn.commit()
        return row

    def mark_visited(self, url: str, kind: str) -> None:
        self.conn.execute("insert or ignore into visited(url,kind) values(?,?)", (url, kind))
        self.conn.commit()

    def mark_failed(self, url: str, error: str) -> None:
        self.conn.execute("insert or replace into failed(url,error) values(?,?)", (url, error[:500]))
        self.conn.commit()


class RawStore:
    def __init__(self, html_dir: str) -> None:
        self.html_dir = Path(html_dir)
        self.html_dir.mkdir(parents=True, exist_ok=True)

    def save_html(self, site: str, url_slug: str, html: str) -> str:
        path = self.html_dir / f"{site}_{url_slug}.html"
        path.write_text(html, encoding="utf-8")
        return str(path)


def append_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
