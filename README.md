# Ecommerce Tool Catalog Scraper

Build a Python 3.11+ scraping framework for public product/catalog pages of tool-brand websites. Do **not** build one hardcoded script. Use a shared crawler plus one adapter per website.

## Target sites

| key | start_url | strategy |
|---|---|---|
| totalbusiness | https://www.totalbusiness.com/ | JS warning visible; use requests first, Playwright fallback. Categories are `/products/...`; products are `/product/<slug>/<code>`. |
| dewalt | https://www.dewalt.com/en-us | Next.js/menu-tab site; use Playwright. Open Products menu and collect every tab, not only active tab. |
| tolsen | https://www.tolsentools.com/product-categories/ | WooCommerce-style; use requests first. Category pages are `/product-category/.../`; products are `/product/.../`. |
| emtop | https://www.emtop.com/products | Similar to TOTAL; JS warning visible. Use Playwright fallback. |
| wokin | https://www.wokintools.com/products/ | WooCommerce-style; use requests first. Category pages are `/product-category/.../`; products are `/product/.../`. |
| crown_tools_eu | https://crown-tools-eu.com/en/ | Structured category navigation in HTML; use requests first. |
| dcktool | https://www.dcktool.com/ | Product center uses `product?cid=...`; details use `/product/detail/<id>`. Use requests first, Playwright fallback. |
| delitools | https://www.delitoolsglobal.com/ | Large category tree in HTML; use requests first, Playwright fallback. |
| bosch | https://www.bosch.com/ | Corporate discovery only. Find product/tools/professional links, then hand off to Bosch Professional. |
| bosch_professional | https://www.bosch-professional.com/in/en/ | Main Bosch tools catalog. Use requests first, Playwright fallback for filters/loading. |
| ronix | https://ronixtools.com/en/ | Huge category taxonomy; use requests first, Playwright fallback for product cards. |

## Goal

For every site:

1. collect all category and sub-category URLs;
2. collect product URLs from every category page, including pagination/load-more/infinite-scroll;
3. visit product pages;
4. extract product title, SKU/model/order number, brand, category path, description, specs/features, image URLs;
5. save description as both raw HTML and clean text;
6. download product images;
7. export to JSONL, CSV, XLSX, and SQLite;
8. support resume and failed URL logging.

## Data schema

```json
{
  "site": "",
  "brand": "",
  "category_path": [],
  "category_url": "",
  "product_url": "",
  "title": "",
  "sku": "",
  "model": "",
  "description_html": "",
  "description_text": "",
  "features": [],
  "specifications": {},
  "image_urls": [],
  "image_paths": [],
  "raw_html_path": "",
  "scraped_at": ""
}
```

## Required stack

Use:

```txt
playwright
beautifulsoup4
lxml
httpx
pandas
openpyxl
pyyaml
python-slugify
tenacity
```

## Project layout

```text
ecom_scraper/
  README.md
  requirements.txt
  config/sites.yaml
  src/
    main.py
    crawler.py
    fetcher.py
    browser.py
    storage.py
    exporters.py
    images.py
    urls.py
    extractors/
      base.py
      generic.py
      totalbusiness.py
      dewalt.py
      tolsen.py
      emtop.py
      wokin.py
      crown_tools_eu.py
      dcktool.py
      delitools.py
      bosch.py
      bosch_professional.py
      ronix.py
  data/
    html/
    images/
    products.jsonl
    products.csv
    products.xlsx
    products.sqlite
    crawl_state.sqlite
    failed_urls.jsonl
```

## Crawler rules

- Normalize URLs: absolute URLs, no tracking params, no fragments, dedupe trailing slash variants.
- Keep crawl state in SQLite: pending, visited, failed, product_urls, category_urls.
- Save raw HTML for every category and product page.
- Use `httpx` first when possible; use Playwright when:
  - JS warning appears,
  - product/category links are missing from static HTML,
  - menu tabs must be clicked,
  - pagination/load-more/infinite scroll is needed.
- Respect robots.txt when `--respect-robots` is enabled.
- Use delay, timeout, retries, and exponential backoff.
- Do not bypass CAPTCHA, login, paywall, or anti-bot systems.

## Extractor interface

```python
class BaseExtractor:
    def category_links(self, html, url) -> list[str]: ...
    def product_links(self, html, url) -> list[str]: ...
    def next_pages(self, html, url) -> list[str]: ...
    def product_data(self, html, url) -> dict: ...
```

`generic.py` should try:

- JSON-LD Product/BreadcrumbList;
- OpenGraph/meta tags;
- breadcrumbs;
- `h1`;
- product cards;
- links containing `/product`, `/products`, `/product-category`, `/category`, `/tools`;
- image `src`, `srcset`, `data-src`, lazy images, Next.js image URLs;
- tables, bullet lists, and sections named Features, Specifications, Technical Parameters, Additional data.

## Site-specific notes

### totalbusiness
Start from homepage and `/products/*`. Category pages contain result counts and product cards. Product pages contain product code, technical parameters, and images. Use Playwright if static HTML is incomplete.

### dewalt
Use Playwright. Open Products menu and collect every main tab:
Power Tools, Hand Tools, Outdoor, Storage & Organization, Safety Equipment & PPE, Systems, Anchors & Fasteners.
For each tab, collect category/sub-category links, then crawl `/en-us/products/...` pages and product detail pages.

### tolsen
Use this as the pilot site first. Category index is clean. Category pages show result count, product cards, SKU/stock number, description snippets, pagination. Product pages contain breadcrumb, images, SKU, category, attachments, related products.

### emtop
Similar to TOTAL. Static HTML exposes top categories, but JS warning appears, so implement Playwright fallback.

### wokin
WooCommerce-style. Product index/category pages show result count, product cards, SKU, quick-view links, and pagination. Use static first.

### crown_tools_eu
Homepage/category pages expose large nested tool taxonomy. Collect category links from navigation blocks, then collect product pages from category pages.

### dcktool
Product center lists sidebar categories and products. Category URLs use `product?cid=...`; product details use `/product/detail/<id>`. Product pages expose specs/features/images.

### delitools
Navigation exposes product lines such as DC Power Tools, Red Series, Yellow Series, Home Series, Garden Series, plus many subcategories. Crawl category tree and product pages; use Playwright only if static HTML misses product cards.

### bosch
Use as discovery root only. Detect links containing products, services, tools, professional, power tools, catalog. Main crawling should happen in `bosch_professional`.

### bosch_professional
Main catalog. Category pages list tool categories, filters, product count, product cards. Product pages expose breadcrumbs, order number, bullet features, images, price/availability, and technical data tables.

### ronix
Homepage/category pages expose a very large category taxonomy. Crawl sidebars and product-category pages. Use Playwright fallback if product cards are hidden or dynamically rendered.

## CLI

```bash
python -m src.main --site tolsen --dry-run
python -m src.main --site dewalt --max-products 50 --download-images
python -m src.main --site bosch_professional --download-images
python -m src.main --site all --resume --output-format all --download-images
```

## Run commands (full quick-start)

```bash
# 1) clone + enter
git clone https://github.com/supplysenterprise-beep/ecommerce_scraper.git
cd ecommerce_scraper

# 2) create virtual env
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) install dependencies
pip install -U pip
pip install -r requirements.txt

# 4) Playwright browser install (needed for JS/dynamic sites)
playwright install

# 5) smoke test
python -m src.main --site tolsen --dry-run --max-pages 5

# 6) scrape example
python -m src.main --site tolsen --max-products 20 --output-format all --download-images

# 7) scrape all sites with resume
python -m src.main --site all --resume --output-format all --download-images
```

## GUI (Streamlit)

```bash
# from repo root and active venv
streamlit run src/gui.py
```

Then open the URL shown in terminal (usually `http://localhost:8501`), choose site/options, and click **Run scraper**.

Options:

```text
--site
--dry-run
--resume
--download-images
--max-pages
--max-products
--output-format jsonl,csv,xlsx,sqlite,all
--delay
--timeout
--headless
--respect-robots
```

## Development order

1. Build CLI, config loader, URL normalizer, storage.
2. Build generic crawler and generic extractor.
3. Implement TOLSEN end-to-end first.
4. Add WOKIN.
5. Add TOTAL and EMTOP.
6. Add DEWALT Playwright menu-tab crawler.
7. Add Bosch Professional, then Bosch discovery.
8. Add CROWN, DCK, DELI, RONIX.
9. Add exporters, image downloader, tests.

## Acceptance test

For each site, `--dry-run --max-pages 20` must output category URLs and product URLs.
For TOLSEN, WOKIN, TOTAL, DCK, and Bosch Professional, scrape at least 5 product pages each and export valid JSONL/CSV/SQLite rows.
Descriptions must include both `description_html` and `description_text`.
Images must be downloaded when `--download-images` is used.
Resume must continue from `crawl_state.sqlite` without re-scraping visited URLs.
