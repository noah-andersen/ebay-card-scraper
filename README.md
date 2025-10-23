# eBay Card Scraper

A Python tool for scraping graded Pokemon card data from eBay. This scraper searches for graded Pokemon cards based on the grading company (PSA, BGS, CGC, SGC) and downloads images from the listings.

## Features

- Search eBay for graded Pokemon cards by grading company
- Filter searches by specific card names
- Download high-resolution images from eBay listings
- Organized output directory structure
- Command-line interface for easy usage
- Support for multiple grading companies (PSA, BGS, CGC, SGC)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/noah-andersen/ebay-card-scraper.git
cd ebay-card-scraper
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Basic usage - search for PSA graded Pokemon cards:
```bash
python ebay_card_scraper.py PSA
```

Search for a specific card:
```bash
python ebay_card_scraper.py PSA --card "Charizard"
```

Customize the number of listings and output directory:
```bash
python ebay_card_scraper.py BGS --card "Pikachu" --max-listings 10 --output-dir my_images
```

### Available Grading Companies

- **PSA** - Professional Sports Authenticator
- **BGS** - Beckett Grading Services
- **CGC** - Certified Guaranty Company
- **SGC** - Sportscard Guaranty

### Python API

You can also use the scraper as a Python module:

```python
from ebay_card_scraper import EbayCardScraper

# Create scraper instance
scraper = EbayCardScraper(output_dir="my_images")

# Search and download
results = scraper.scrape_and_download(
    grading_company="PSA",
    card_name="Charizard",
    max_listings=5
)

# View results
print(f"Downloaded {results['total_images']} images from {results['listings_downloaded']} listings")
```

### Advanced Usage

Search for listings without downloading:
```python
scraper = EbayCardScraper()
listings = scraper.search_graded_cards("PSA", "Pikachu", max_results=10)

for listing in listings:
    print(f"{listing['title']} - {listing['price']}")
```

Download images from a specific listing URL:
```python
scraper = EbayCardScraper()
saved_files = scraper.download_listing_images(
    "https://www.ebay.com/itm/...",
    card_name="My Card"
)
```

## Command Line Arguments

- `grading_company` (required): The grading company to search for (PSA, BGS, CGC, or SGC)
- `--card`: Specific card name to search for (optional)
- `--max-listings`: Maximum number of listings to process (default: 5)
- `--output-dir`: Directory to save images (default: ebay_images)

## Output Structure

Downloaded images are organized in the following structure:
```
ebay_images/
├── Card_Name_1/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
├── Card_Name_2/
│   ├── image_001.jpg
│   └── ...
```

## Requirements

- Python 3.7+
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0

## Notes

- The scraper includes polite delays between requests to avoid overwhelming eBay's servers
- Images are downloaded in the highest available resolution
- The tool respects eBay's robots.txt and terms of service
- Use responsibly and in accordance with eBay's policies

## License

This project is provided as-is for educational and personal use.
