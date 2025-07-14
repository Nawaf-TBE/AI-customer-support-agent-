# Aven Support Page Scraper

A comprehensive scraping tool that uses Exa.ai's advanced capabilities to recursively crawl and extract content from Aven's support documentation.

## Features

- **Intelligent Crawling**: Uses Exa.ai's neural search and subpage crawling
- **Content Processing**: Converts HTML to clean, structured text chunks
- **Domain-Focused**: Stays within the support domain for targeted scraping
- **Multiple Export Formats**: JSON, CSV, and Markdown output
- **Rate Limiting**: Respects API limits with intelligent throttling
- **Error Recovery**: Robust retry logic and error handling
- **Metadata Extraction**: Captures titles, URLs, publication dates, and more

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API key:
```bash
cp config.template .env
# Edit .env and add your Exa.ai API key
```

3. Run the scraper:
```bash
python aven_scraper.py
```

## Configuration

Edit the configuration in `.env` or pass parameters directly:

- `EXA_API_KEY`: Your Exa.ai API key
- `MAX_SUBPAGES`: Maximum pages to crawl (default: 50)
- `REQUESTS_PER_MINUTE`: Rate limiting (default: 30)
- `CHUNK_SIZE`: Text chunk size for processing (default: 1000)
- `OUTPUT_DIR`: Directory for scraped data (default: ./scraped_data)

## Output Structure

```
scraped_data/
├── aven_support_raw.json          # Raw scraped data
├── aven_support_processed.json    # Processed text chunks
├── aven_support_summary.csv       # Summary statistics
└── content_chunks/                # Individual markdown files
    ├── page_001.md
    ├── page_002.md
    └── ...
```

## Usage Examples

### Basic Usage
```python
from aven_scraper import AvenScraper

scraper = AvenScraper(api_key="your_exa_key")
results = scraper.scrape_support_pages()
```

### Advanced Configuration
```python
scraper = AvenScraper(
    api_key="your_exa_key",
    max_subpages=100,
    chunk_size=1500,
    target_content=["faq", "guide", "tutorial", "help"]
)
results = scraper.scrape_support_pages()
```

## API Integration

This tool leverages Exa.ai's powerful features:
- **Neural Search**: Semantic content discovery
- **Subpage Crawling**: Recursive link following
- **Content Extraction**: Clean HTML-to-text conversion
- **Domain Filtering**: Targeted scraping within support domains 