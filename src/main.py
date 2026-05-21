from __future__ import annotations

import argparse
from importlib import import_module

import yaml

from src.crawler import Crawler
from src.exporters import export_rows


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--download-images", action="store_true")
    p.add_argument("--max-pages", type=int, default=0)
    p.add_argument("--max-products", type=int, default=0)
    p.add_argument("--output-format", default="all")
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--timeout", type=float, default=20.0)
    p.add_argument("--headless", action="store_true")
    p.add_argument("--respect-robots", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = yaml.safe_load(open("config/sites.yaml", "r", encoding="utf-8"))["sites"]
    keys = list(cfg.keys()) if args.site == "all" else [args.site]
    all_rows = []
    for key in keys:
        extractor_module = import_module(f"src.extractors.{key}")
        extractor = extractor_module.Extractor()
        crawler = Crawler(key, cfg[key], extractor, args)
        rows = crawler.run()
        crawler.close()
        all_rows.extend(rows)
    if not args.dry_run:
        export_rows(all_rows, "data", args.output_format)


if __name__ == "__main__":
    main()
