# Scraper

An async, rule-based web scraper that extracts structured content from target URLs using CSS class filtering. Output is written as JSON to `output_scrape/`.

## Features

- **Class-filtered extraction** — pull only the elements you care about, defined per site in `extraction_settings.json`
- **Structured JSON output** — each scraped URL produces `{ url, content, extras }` written atomically to `output_scrape/`
- **Async HTTP/2** — single shared `httpx` client with connection pooling, stealth headers, 10 MB body cap, and redirect logging
- **Rich console** — live progress bar with spinner, URL tracking, and structured logging via `rich`
- **Environment-driven config** — `pydantic-settings` reads `SCRAPER_*` vars from the repo-root `.env` file
- **SOLID architecture** — Strategy, Factory, Facade, and Sink patterns; all core seams are interface-driven

## Project Structure

```
apps/scraper/
├── extraction_settings.json   # URLs and per-site CSS class rules
├── output_scrape/             # Generated JSON output (git-ignored)
├── config.py                  # ScraperSettings (pydantic-settings) + StealthConfig
├── main.py                    # Entry point — wires dependencies, runs loop
│
├── core/
│   ├── logging_setup.py       # RichHandler with force=True, silences httpx noise
│   ├── settings_loader.py     # Validates + loads extraction_settings.json → ExtractionSettings
│   ├── site_resolver.py       # Maps URL host tokens → site key (e.g. "ynet")
│   └── utils.py               # safe_name() — length-capped, hash-suffixed filename stem
│
├── models/
│   ├── interfaces.py          # BaseParser, BaseScraper, BaseSiteResolver, BaseParserProvider, BaseSink
│   ├── result.py              # ParseResult(content: list[str], extras: dict[str, list[str]])
│   └── settings.py            # ExtractionSettings, SiteExtractionRule (frozen, MappingProxyType)
│
└── services/
    ├── facade.py              # ScrapingFacade — orchestrates fetch → parse pipeline
    ├── parser.py              # TextContentParser, ClassFilteredParser (Strategy)
    ├── parser_factory.py      # RuleBasedParserProvider (Factory)
    ├── scraper.py             # HttpScraper — async context manager, shared client
    └── sink.py                # JsonFileSink — atomic file writes (BaseSink implementation)
```

## Configuration

### Environment variables

Settings are read from `<repo-root>/.env` (copy `.env.example` to get started):

| Variable | Default | Description |
|---|---|---|
| `SCRAPER_TIMEOUT_SECONDS` | `30.0` | Per-request HTTP timeout |
| `SCRAPER_ACCEPT_LANGUAGE` | `en-US,en;q=0.9,he;q=0.8` | `Accept-Language` header value |
| `SCRAPER_PROXY` | _(none)_ | Optional HTTP/SOCKS proxy URL |

### Extraction rules

Edit `extraction_settings.json` to control which URLs are scraped and how:

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
|---|---|
| `url_scraping` | List of `http`/`https` URLs to scrape (validated at startup) |
| `limitation_by_class` | Per-site CSS classes whose text forms the `content` array |
| `extra_data_by_class` | Per-site CSS classes whose text forms the `extras` dict (keyed by class name) |

The site key (e.g. `"example"`) is matched against dot-separated hostname tokens — no code changes needed to add a new site. If no rule exists for a URL's host, the scraper falls back to full-page text extraction.

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
  "extras": {
    "tagName": ["breaking news", "politics"]
  }
}
```

`extras` is keyed by the CSS class name so consumers know the origin of each extracted value.

## Setup

```bash
# From the repo root
cp .env.example .env   # then edit .env as needed
uv sync
```

## Usage

```bash
cd apps/scraper
python main.py
```

## Dependencies

| Package | Purpose |
|---|---|
| `httpx[http2]` | Async HTTP/2 client |
| `beautifulsoup4` | HTML parsing |
| `aiofiles` | Async file I/O |
| `rich` | Progress bar and structured logging |
| `pydantic-settings` | Typed config from environment / `.env` |
