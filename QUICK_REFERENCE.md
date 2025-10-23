# Quick Reference Guide

## Installation
```bash
git clone https://github.com/noah-andersen/ebay-card-scraper.git
cd ebay-card-scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Basic Usage

### Command Line

```bash
# eBay only
python main.py --marketplace ebay --company PSA --grade 10 --max-results 50

# Mercari only
python main.py --marketplace mercari --company BGS --grade 9.5 --max-results 30

# Both marketplaces
python main.py --marketplace both --company CGC --grade 10 --max-results 40

# Specific card
python main.py --marketplace ebay --company PSA --grade 10 --card-name Charizard --max-results 20

# Sold listings (eBay only)
python main.py --marketplace ebay --company PSA --grade 10 --sold-only --max-results 25
```

### Python API

```python
from scrapers import EbayScraper, MercariScraper

# eBay
ebay = EbayScraper()
ebay.search_graded_cards('PSA', 10, max_results=50)

# Mercari
mercari = MercariScraper()
mercari.search_graded_cards('BGS', 9.5, card_name='Pikachu', max_results=30)

# Custom output
scraper = EbayScraper(output_dir='./my_data')
scraper.search_graded_cards('CGC', 9, max_results=25)
```

## Available Options

### Marketplaces
- `ebay` - eBay marketplace
- `mercari` - Mercari marketplace
- `both` - Search both marketplaces

### Grading Companies
- `PSA` - Professional Sports Authenticator
- `BGS` or `BECKETT` - Beckett Grading Services
- `CGC` - Certified Guaranty Company

### Grades
- 1-10 for PSA and CGC
- 1-10 or 9.5 for BGS/Beckett

### Additional Flags
- `--card-name` - Search for specific card (e.g., "Charizard")
- `--max-results` - Maximum results per marketplace (default: 50)
- `--sold-only` - eBay sold listings only
- `--output-dir` - Custom output directory

## Output Structure

```
data/
├── ebay/
│   ├── images/
│   │   ├── PSA_10_Charizard_123456.jpg
│   │   └── PSA_10_Pikachu_789012.jpg
│   └── metadata.csv
└── mercari/
    ├── images/
    │   ├── BGS_9.5_Mewtwo_abc123.jpg
    │   └── BGS_9.5_Blastoise_def456.jpg
    └── metadata.csv
```

## Metadata CSV Columns

- `marketplace` - ebay or mercari
- `listing_id` - Unique listing ID
- `card_name` - Card title/name
- `grading_company` - PSA, BGS, or CGC
- `grade` - Card grade
- `price` - Listed or sold price
- `image_url` - Original image URL
- `image_path` - Local file path
- `timestamp` - When scraped
- `sold` - If sold (eBay only)

## Configuration

Edit `config.py` to customize:

```python
# Request settings
TIMEOUT = 60  # Request timeout in seconds
REQUEST_DELAY_MIN = 3  # Min delay between requests
REQUEST_DELAY_MAX = 7  # Max delay between requests

# Image settings
IMAGE_FORMAT = 'jpg'
IMAGE_QUALITY = 90

# Output
OUTPUT_DIR = './data'
MAX_RESULTS = 50  # Default max results
```

## Examples

Run interactive examples:
```bash
python examples.py
```

Available examples:
1. Single marketplace
2. Multiple marketplaces
3. Specific card search
4. Sold listings
5. Custom output directory
6. Iterate through grades

## Troubleshooting

### No results found
- Increase timeout in `config.py`
- Check internet connection
- Try different search terms
- Some marketplaces may block automated requests

### Connection errors
- Increase `TIMEOUT` in `config.py`
- Check network stability
- Try fewer concurrent requests

### Images not downloading
- Check disk space
- Verify write permissions
- Check `scraper.log` for errors

### Import errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version (3.7+ required)

## Logging

Each scraper creates a log file:
- `scraper.log` - Main log file
- Contains timestamps, actions, errors
- Review for debugging issues

## Best Practices

1. **Start small**: Test with `--max-results 5` first
2. **Respect rate limits**: Don't set delays too low
3. **Use specific searches**: Add card names for better results
4. **Check logs**: Review `scraper.log` for issues
5. **Back up data**: Keep copies of successful scrapes

## Quick Tests

```bash
# Test eBay (5 results)
python main.py --marketplace ebay --company PSA --grade 10 --max-results 5

# Test Mercari (5 results)
python main.py --marketplace mercari --company BGS --grade 9 --max-results 5

# Test both (5 results each)
python main.py --marketplace both --company CGC --grade 10 --max-results 5
```

## Getting Help

1. Check `README.md` for detailed documentation
2. Review `TROUBLESHOOTING.md` for common issues
3. Check `scraper.log` for error messages
4. Read `CONSOLIDATION_SUMMARY.md` for architecture details
5. Run `python main.py --help` for CLI options

## Adding New Marketplaces

See `scrapers/base_scraper.py` for the base class template. Create a new scraper:

```python
from scrapers.base_scraper import BaseScraper

class NewScraper(BaseScraper):
    def __init__(self, output_dir=None):
        super().__init__('marketplace_name', output_dir)
    
    def _build_search_url(self, grading_company, grade, card_name=None):
        # Build URL
        pass
    
    def _extract_listing_data(self, listing_soup):
        # Extract data
        pass
    
    def search_graded_cards(self, grading_company, grade, **kwargs):
        # Search logic
        pass
```

Then import and use in `main.py`.
