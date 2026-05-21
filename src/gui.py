from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st
import yaml


def load_sites() -> list[str]:
    cfg = yaml.safe_load(Path("config/sites.yaml").read_text(encoding="utf-8"))
    return list(cfg.get("sites", {}).keys())


def build_command(site: str, dry_run: bool, resume: bool, download_images: bool, max_pages: int, max_products: int, output_format: str, delay: float, timeout: float, headless: bool, respect_robots: bool) -> list[str]:
    cmd = [sys.executable, "-m", "src.main", "--site", site]
    if dry_run:
        cmd.append("--dry-run")
    if resume:
        cmd.append("--resume")
    if download_images:
        cmd.append("--download-images")
    if max_pages > 0:
        cmd.extend(["--max-pages", str(max_pages)])
    if max_products > 0:
        cmd.extend(["--max-products", str(max_products)])
    cmd.extend(["--output-format", output_format, "--delay", str(delay), "--timeout", str(timeout)])
    if headless:
        cmd.append("--headless")
    if respect_robots:
        cmd.append("--respect-robots")
    return cmd


def main() -> None:
    st.set_page_config(page_title="Ecommerce Scraper GUI", layout="wide")
    st.title("Ecommerce Tool Catalog Scraper")
    st.caption("CLI wrapper for running scrapes without typing long commands")

    sites = load_sites()
    with st.sidebar:
        site = st.selectbox("Site", options=sites + ["all"], index=0)
        output_format = st.selectbox("Output format", options=["all", "jsonl", "csv", "xlsx", "sqlite", "jsonl,csv"])
        max_pages = st.number_input("Max pages (0 = unlimited)", min_value=0, value=20, step=1)
        max_products = st.number_input("Max products (0 = unlimited)", min_value=0, value=20, step=1)
        delay = st.number_input("Delay (seconds)", min_value=0.0, value=0.5, step=0.1)
        timeout = st.number_input("Timeout (seconds)", min_value=1.0, value=20.0, step=1.0)
        dry_run = st.checkbox("Dry run", value=False)
        resume = st.checkbox("Resume", value=True)
        download_images = st.checkbox("Download images", value=False)
        headless = st.checkbox("Headless", value=True)
        respect_robots = st.checkbox("Respect robots.txt", value=False)

    cmd = build_command(
        site,
        dry_run,
        resume,
        download_images,
        int(max_pages),
        int(max_products),
        output_format,
        float(delay),
        float(timeout),
        headless,
        respect_robots,
    )

    st.code(" ".join(cmd), language="bash")

    if st.button("Run scraper", type="primary"):
        with st.spinner("Running scraper..."):
            result = subprocess.run(cmd, capture_output=True, text=True)
        st.subheader("Exit status")
        st.write(result.returncode)
        st.subheader("STDOUT")
        st.text(result.stdout or "(empty)")
        st.subheader("STDERR")
        st.text(result.stderr or "(empty)")


if __name__ == "__main__":
    main()
