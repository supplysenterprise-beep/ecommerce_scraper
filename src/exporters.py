from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


def export_rows(rows: list[dict], base_dir: str, output_format: str) -> None:
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    formats = {"jsonl", "csv", "xlsx", "sqlite"} if output_format == "all" else set(output_format.split(","))
    if "jsonl" in formats:
        with open(f"{base_dir}/products.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    df = pd.DataFrame(rows)
    if "csv" in formats:
        df.to_csv(f"{base_dir}/products.csv", index=False)
    if "xlsx" in formats:
        df.to_excel(f"{base_dir}/products.xlsx", index=False)
    if "sqlite" in formats:
        con = sqlite3.connect(f"{base_dir}/products.sqlite")
        df.to_sql("products", con, if_exists="replace", index=False)
        con.close()
