# Scraper

An async, rule-based web scraper that extracts structured content from target URLs using CSS class filtering. Output is written as JSON to `output_scrape/`.

## Features

- **Class-filtered extraction** — pull only the elements you care about, defined per site in `extraction_settings.json`
- **Structured JSON output** — each scraped URL produces `{ url, content, extras }` in `output_scrape/`
- **Async HTTP** — lightweight `httpx` client with HTTP/2, stealth headers, and redirect following (no browser dependency)
- **Rich console** — live progress bar with spinner, URL tracking, and structured logging via `rich`
- **SOLID architecture** — Strategy, Factory, and Facade patterns; all core seams are interface-driven

## Project Structure

```
apps/scraper/
├── extraction_settings.json   # URLs and per-site CSS class rules
├── output_scrape/              # Generated JSON output (git-ignored)
├── config.py                  # StealthConfig — rotating User-Agent + headers
├── main.py                    # Entry point — wires dependencies, runs loop
│
├── core/
│   ├── logging_setup.py       # Configures RichHandler for structured logging
│   ├── settings_loader.py     # Loads extraction_settings.json → ExtractionSettings
│   ├── site_resolver.py       # Maps URL host → site key (e.g. "ynet")
│   └── utils.py               # safe_name() for filesystem-safe filenames
│
├── models/
│   ├── interfaces.py          # BaseParser, BaseScraper, BaseSiteResolver, BaseParserProvider
│   ├── result.py              # ParseResult(content, extras)
│   └── settings.py            # ExtractionSettings, SiteExtractionRule dataclasses
│
└── services/
    ├── facade.py              # Scraper — orchestrates fetch → parse pipeline
    ├── parser.py              # TextContentParser, ClassFilteredParser (Strategy)
    ├── parser_factory.py      # RuleBasedParserProvider (Factory)
    └── scraper.py             # HttpScraper (httpx-based)
```

## Configuration

Edit `extraction_settings.json` to add URLs and per-site extraction rules:

```json
{
    "url_scraping": [
        "https://www.example.com/article/123"
    ],
    "limitation_by_class": {
        "example": ["mainTitleWrapper", "text_editor_paragraph"]
    },
    "extra_data_by_class": {
        "example": ["tagName"]
    }
}
```

| Field | Description |
|-------|-------------|
| `url_scraping` | List of URLs to scrape |
| `limitation_by_class` | Per-site CSS classes whose text forms the `content` array |
| `extra_data_by_class` | Per-site CSS classes whose text forms the `extras` array |

The site key (e.g. `"example"`) is matched against the URL hostname — no code changes needed to add a new site.

If no rule exists for a URL's host, the scraper falls back to full-page text extraction.

## Output Format

Each URL produces a file in `output_scrape/<safe_url>.json`:

```json
{
  "url": "https://www.example.com/article/123",
  "content": [
    "Article title",
    "Subtitle",
    "First paragraph..."
  ],
  "extras": [
    "breaking news",
    "politics"
  ]
}
```

## Setup

```bash
uv sync
# or
pip install -e .
```

## Usage

```bash
python main.py
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `httpx[http2]` | Async HTTP client |
| `bs4` | HTML parsing |
| `aiofiles` | Async file I/O |
| `rich` | Progress bar and structured logging |
