# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **uv workspace** (`ragpractice`) structured for a custom RAG (Retrieval-Augmented Generation) pipeline. Currently it has one active app: `apps/scraper` — an async, rule-based web scraper that feeds content into the RAG pipeline.

## Commands

All commands are run from the repo root unless noted.

```bash
# Install all workspace dependencies
uv sync

# Run the scraper (from apps/scraper/)
cd apps/scraper && python main.py

# Lint (ruff is configured in root pyproject.toml)
uv run ruff check .
uv run ruff check --fix .

# Format
uv run ruff format .
```

There are no tests yet. Python version is 3.12 (pinned in `.python-version`).

## Architecture

### Workspace layout

The root `pyproject.toml` declares a uv workspace with `members = ["apps/*"]`. Each app has its own `pyproject.toml` with its own dependencies. The root-level `main.py` is a placeholder stub.

### `apps/scraper` — the active app

The scraper uses three classic patterns together:

- **Strategy** — `BaseParser` implementations (`TextContentParser`, `ClassFilteredParser`) are interchangeable at runtime
- **Factory** — `RuleBasedParserProvider` selects the right parser strategy based on the URL's resolved site key
- **Facade** — `Scraper` (in `services/facade.py`) is the single entry point; it wires fetch → parse and shields `main.py` from implementation details

**Data flow:**

```
main.py
  └─ loads ExtractionSettings from extraction_settings.json
  └─ wires: HttpScraper + DomainKeywordSiteResolver + RuleBasedParserProvider → Scraper (facade)
  └─ for each URL:
       Scraper.scrape(url)
         ├─ HttpScraper.fetch_html(url)       # httpx async, stealth headers
         ├─ RuleBasedParserProvider.for_url(url)
         │    └─ DomainKeywordSiteResolver.resolve(url) → site key
         │    └─ picks ClassFilteredParser (if rule exists) or TextContentParser (fallback)
         └─ parser.parse(html) → ParseResult(content, extras)
  └─ writes output_scrape/<safe_url>.json
```

**Key seams (all interface-driven, easy to swap):**

| Interface | Location | Purpose |
|---|---|---|
| `BaseScraper` | `models/interfaces.py` | HTTP fetch strategy |
| `BaseParser` | `models/interfaces.py` | HTML parse strategy |
| `BaseSiteResolver` | `models/interfaces.py` | URL → site key mapping |
| `BaseParserProvider` | `models/interfaces.py` | Factory that returns the right parser |

### Configuration — `extraction_settings.json`

Controls which URLs to scrape and what CSS classes to extract per site. The site key (e.g. `"ynet"`) is matched by `DomainKeywordSiteResolver` against the URL hostname. Adding a new site requires only a new entry in this JSON file — no code changes.

### Output

`output_scrape/` is gitignored. Each URL produces `<safe_url>.json` with `{ url, content: [...], extras: [...] }`.

## Linting rules (ruff)

Configured in root `pyproject.toml`. Notable active rules: `E/W` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear), `UP` (pyupgrade), `T201` (no bare `print` — use `logging`), `ARG001` (unused function args). Line length (`E501`) is ignored.
