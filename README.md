# Graded Pokemon Card Scraper

A Python-based web scraper for collecting image data of graded Pokemon cards from multiple marketplaces. This tool searches for graded cards by grading company (PSA, BGS, CGC) and grade level, then saves the image data for analysis or training purposes.

## Features

- **Multi-marketplace support**: eBay and Mercari
- Search for graded Pokemon cards by:
  - Grading company (PSA, BGS, CGC)
  - Grade level (1-10)
  - Card name/keywords
- Download and save card images
- Store metadata (grade, grading company, price, listing details)
- Export data to CSV for easy analysis
- Built-in rate limiting to respect marketplace servers
- Modular architecture for easy marketplace additions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/noah-andersen/ebay-card-scraper.git
cd ebay-card-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

Search a single marketplace:
```bash
# Search eBay for PSA 10 cards
python main.py --marketplace ebay --company PSA --grade 10 --max-results 50

# Search Mercari for BGS 9.5 Charizard
python main.py --marketplace mercari --company BGS --grade 9.5 --card-name Charizard --max-results 20
```

Search both marketplaces:
```bash
# Search both eBay and Mercari for CGC 10 cards
python main.py --marketplace both --company CGC --grade 10 --max-results 50
```

Search eBay sold listings:
```bash
# eBay sold/completed listings only
python main.py --marketplace ebay --company PSA --grade 10 --sold-only --max-results 30
```

### Python API

```python
from scrapers import EbayScraper, MercariScraper

# eBay scraper
ebay = EbayScraper(output_dir='./data')
ebay.search_graded_cards(
    grading_company='PSA',
    grade=10,
    max_results=50
)

# Mercari scraper
mercari = MercariScraper(output_dir='./data')
mercari.search_graded_cards(
    grading_company='BGS',
    grade=9.5,
    card_name='Charizard',
    max_results=30
)

# Search for specific card
scraper.search_graded_cards(
    grading_company='BGS',
    grade=9.5,
    card_name='Charizard',
    max_results=20
)
```

### Command Line Usage

```bash
# Search for PSA 10 cards
python main.py --company PSA --grade 10 --max-results 50

# Search for BGS 9.5 Charizard cards
python main.py --company BGS --grade 9.5 --card-name Charizard --max-results 20

# Search all grades for a specific company
python main.py --company CGC --all-grades --max-results 100
```

## Project Structure

```
ebay-card-scraper/
├── scrapers/            # Marketplace scrapers
│   ├── __init__.py      # Package initialization
│   ├── base_scraper.py  # Abstract base class
│   ├── ebay_scraper.py  # eBay implementation
│   └── mercari_scraper.py  # Mercari implementation
├── main.py              # CLI entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── data/                # Output directory (created automatically)
│   ├── ebay/            # eBay downloads
│   │   ├── images/      # Card images
│   │   └── metadata.csv # eBay metadata
│   └── mercari/         # Mercari downloads
│       ├── images/      # Card images
│       └── metadata.csv # Mercari metadata
├── README.md
├── QUICKSTART.md        # Quick start guide
└── TROUBLESHOOTING.md   # Common issues
```

## Output Format

Images are saved with the naming convention:
```
{grading_company}_{grade}_{card_name}_{listing_id}.jpg
```

Metadata CSV includes:
- `marketplace`: ebay or mercari
- `listing_id`: Unique listing identifier
- `card_name`: Name/title of the card
- `grading_company`: PSA, BGS, or CGC
- `grade`: Card grade (1-10 or 9.5 for BGS)
- `price`: Current or sold price
- `image_url`: Original image URL
- `image_path`: Local path to saved image
- `timestamp`: When the data was scraped
- `sold`: Whether listing was sold (eBay only)

## Configuration

Edit `config.py` to customize:
- Request timeouts and delays
- Image format and quality
- Output directories
- Grading companies supported

## Rate Limiting

The scraper includes built-in delays to avoid overwhelming marketplace servers:
- 3-7 second delay between page requests (configurable)
- Random delays to appear more human-like
- Respect for marketplace rate limits

## Adding New Marketplaces

To add a new marketplace, create a new scraper class that inherits from `BaseScraper`:

```python
from scrapers.base_scraper import BaseScraper

class NewMarketplaceScraper(BaseScraper):
    def __init__(self, output_dir=None):
        super().__init__('marketplace_name', output_dir)
    
    def _build_search_url(self, grading_company, grade, card_name=None):
        # Build marketplace-specific URL
        pass
    
    def _extract_listing_data(self, listing_soup):
        # Extract listing data
        pass
    
    def search_graded_cards(self, grading_company, grade, **kwargs):
        # Implement search logic
        pass
```

## Legal & Ethical Considerations

- This scraper is for educational and research purposes
- Respect marketplace Terms of Service and robots.txt
- Use reasonable rate limiting
- Don't use for commercial purposes without proper authorization
- Consider using official APIs for production use

## Troubleshooting

If you encounter issues:
1. Check `TROUBLESHOOTING.md` for common problems
2. Review scraper logs for error messages
3. Verify your internet connection
4. Try increasing timeouts in `config.py`

Common issues:
- **eBay blocking**: eBay has sophisticated bot detection. Results may be limited.
- **Connection timeouts**: Increase `TIMEOUT` in `config.py`
- **No results found**: Some marketplaces may block automated requests

## Future Enhancements

- [ ] Support for TCGPlayer marketplace
- [ ] Support for more TCGs (Yu-Gi-Oh, Magic: The Gathering)
- [ ] Image quality filtering
- [ ] Duplicate detection across marketplaces
- [ ] Multi-threading for faster scraping
- [ ] Database storage option
- [ ] Price trend analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with eBay's Terms of Service and applicable laws.
