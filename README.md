# eBay Card Scraper

A Python-based web scraper for collecting image data of graded Pokemon cards from eBay. This tool searches for graded cards by grading company (PSA, BGS, CGC) and grade level, then saves the image data for analysis or training purposes.

## Features

- Search eBay for graded Pokemon cards by:
  - Grading company (PSA, BGS, CGC)
  - Grade level (1-10)
  - Card name/keywords
- Download and save card images
- Store metadata (grade, grading company, price, listing details)
- Export data to CSV for easy analysis
- Built-in rate limiting to respect eBay's servers

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

4. Create a `.env` file (optional for API keys if using eBay API):
```bash
cp .env.example .env
# Edit .env with your credentials if needed
```

## Usage

### Basic Usage

```python
from scraper import EbayScraper

# Initialize scraper
scraper = EbayScraper(output_dir='./data')

# Search for PSA 10 graded Pokemon cards
scraper.search_graded_cards(
    grading_company='PSA',
    grade=10,
    max_results=50
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
├── scraper.py          # Main scraper class
├── main.py             # CLI entry point
├── utils.py            # Helper functions
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── data/              # Output directory for images and CSV
│   ├── images/        # Downloaded card images
│   └── metadata.csv   # Card metadata
└── README.md
```

## Output Format

Images are saved with the naming convention:
```
{grading_company}_{grade}_{card_name}_{listing_id}.jpg
```

Metadata CSV includes:
- `listing_id`: eBay listing ID
- `card_name`: Name/title of the card
- `grading_company`: PSA, BGS, or CGC
- `grade`: Card grade (1-10 or 9.5 for BGS)
- `price`: Current or sold price
- `image_url`: Original eBay image URL
- `image_path`: Local path to saved image
- `timestamp`: When the data was scraped

## Rate Limiting

The scraper includes built-in delays to avoid overwhelming eBay's servers:
- 2-5 second delay between page requests
- Configurable in `config.py`

## Legal & Ethical Considerations

- This scraper is for educational and research purposes
- Respect eBay's Terms of Service and robots.txt
- Use reasonable rate limiting
- Don't use for commercial purposes without proper authorization
- Consider using eBay's official API for production use

## Future Enhancements

- [ ] Support for more TCGs (Yu-Gi-Oh, Magic: The Gathering)
- [ ] eBay API integration for more reliable data
- [ ] Image quality filtering
- [ ] Duplicate detection
- [ ] Multi-threading for faster scraping
- [ ] Database storage option

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with eBay's Terms of Service and applicable laws.
