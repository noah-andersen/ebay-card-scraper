# Quick Start Guide

## Installation

1. **Navigate to the project directory:**
```bash
cd /Users/nandersen/git_repos/ebay-card-scraper
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Basic Usage

### Method 1: Command Line (Easiest)

```bash
# Search for PSA 10 cards (10 results)
python main.py --company PSA --grade 10 --max-results 10

# Search for BGS 9.5 Charizard cards
python main.py --company BGS --grade 9.5 --card-name Charizard --max-results 5

# Search sold listings for CGC 10 cards
python main.py --company CGC --grade 10 --sold-only --max-results 10

# Search all grades for PSA (5 per grade)
python main.py --company PSA --all-grades --max-results-per-grade 5
```

### Method 2: Interactive Examples

```bash
# Run the interactive example script
python example.py
```

### Method 3: Python Code

```python
from scraper import EbayScraper

# Initialize scraper
scraper = EbayScraper(output_dir='./data')

# Search for graded cards
scraper.search_graded_cards(
    grading_company='PSA',
    grade=10,
    max_results=10
)
```

## Output

- **Images:** Saved to `data/images/`
- **Metadata:** Saved to `data/metadata.csv`
- **Logs:** Saved to `scraper.log`

## Common Commands

```bash
# View scraping statistics
python -c "from utils import print_statistics; import config; print_statistics(config.METADATA_FILE)"

# Remove duplicate images
python -c "from utils import deduplicate_images; import config; deduplicate_images(config.IMAGES_DIR, config.METADATA_FILE)"
```

## Tips

1. **Start small:** Use `--max-results 5` for testing
2. **Rate limiting:** Built-in delays prevent overwhelming eBay's servers
3. **Interrupting:** Press Ctrl+C to stop scraping safely
4. **Resuming:** The scraper skips already downloaded listings

## Next Steps

- Customize search queries in `config.py`
- Adjust rate limiting delays
- Export metadata for analysis
- Build a dataset for ML training

## Troubleshooting

**No images downloaded?**
- Check your internet connection
- eBay may have changed their HTML structure
- Try different search terms

**Rate limited?**
- Increase delays in `config.py`
- Wait before retrying

**Import errors?**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`
