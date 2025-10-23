# eBay Graded Cards Scraper - Usage Guide

## ✅ Project Status: FULLY FUNCTIONAL

This Scrapy + Playwright scraper successfully extracts graded Pokemon card listings from eBay, including:
- Card titles and parsed card names
- Grading company (PSA, BGS, CGC, SGC) and grades
- Prices
- Listing URLs
- Card images (automatically downloaded and organized)

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /Users/nandersen/git_repos/ebay-card-scraper
source venv/bin/activate
```

### 2. Run the Scraper
```bash
# Basic usage (default: "PSA 10 Pokemon Card", 5 pages)
scrapy crawl ebay_graded_cards -O output.json

# Custom search query
scrapy crawl ebay_graded_cards -a search_query="Pokemon PSA 10 Charizard" -a max_pages=3 -O charizard_output.json

# Search for specific grading companies
scrapy crawl ebay_graded_cards -a search_query="Pokemon BGS 9.5" -a max_pages=2 -O bgs_output.json
```

## Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `search_query` | "PSA 10 Pokemon Card" | eBay search query |
| `max_pages` | 5 | Maximum number of pages to scrape (240 items per page) |

## Output Structure

### JSON Output
Items are saved with the following fields:
```json
{
  "title": "2018 POKEMON SUN & MOON LOST THUNDER #121 TYRANITAR GX PSA 10 GEM MINT",
  "card_name": "2018 POKEMON SUN & MOON LOST THUNDER #121 TYRANITAR GX",
  "grading_company": "PSA",
  "grade": "10",
  "price": 140.0,
  "listing_url": "https://www.ebay.com/itm/...",
  "image_urls": ["https://i.ebayimg.com/images/g/.../s-l500.jpg"],
  "images": [{"url": "...", "path": "ebay/PSA/2018_POKEMON_SUN_&_MOON_LOST_THUNDER_#121_TYRANITAR_GX_20251023_140329.jpg"}],
  "source": "ebay",
  "scraped_date": "2025-10-23T14:02:21.754867"
}
```

### Downloaded Images
Images are automatically organized in:
```
downloaded_images/
  └── ebay/
      ├── PSA/
      ├── BGS/
      ├── CGC/
      └── SGC/
```

Filenames format: `{card_name}_{timestamp}.jpg`

## Performance

- **Speed**: ~250 items in 10 minutes (~25 items/min)
- **Success Rate**: Successfully bypasses eBay bot detection
- **Image Downloads**: Concurrent downloads with organized storage

## Anti-Bot Detection Features

The scraper includes several measures to avoid detection:
- Custom Chrome 120 user agent
- 1920x1080 viewport
- Disabled automation flags
- Navigator.webdriver property override
- Randomized download delays (2s average)

## Advanced Usage

### Adjust Download Speed
Edit `graded_cards_scraper/settings.py`:
```python
DOWNLOAD_DELAY = 2  # Seconds between requests
CONCURRENT_REQUESTS = 8  # Total concurrent requests
CONCURRENT_REQUESTS_PER_DOMAIN = 4  # Per domain
```

### Change Image Storage Location
Edit `graded_cards_scraper/settings.py`:
```python
IMAGES_STORE = '/custom/path/to/images'
```

### Enable/Disable Headless Mode
Edit `graded_cards_scraper/settings.py`:
```python
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # Set to False to see browser
    "args": [
        "--disable-blink-features=AutomationControlled",
    ],
}
```

## Troubleshooting

### Images Not Downloading
- Check `downloaded_images/` folder exists
- Verify `allowed_domains` includes `ebayimg.com` in spider
- Check pipeline is enabled in settings

### Bot Detection / Challenge Pages
- Increase `DOWNLOAD_DELAY` in settings
- Check user agent is up to date
- Verify anti-automation flags are set

### No Items Scraped
- Check eBay page structure hasn't changed
- Verify selectors in `ebay_spider.py`:
  - Items: `ul.srp-results li`
  - Title: `img::attr(alt)`
  - Price: `*::text` with regex `r'\$[\d,]+\.?\d*'`
  - URL: `a.image-treatment::attr(href)`

## Example Queries

```bash
# PSA 10 Pikachu cards
scrapy crawl ebay_graded_cards -a search_query="Pikachu PSA 10" -O pikachu.json

# Vintage cards
scrapy crawl ebay_graded_cards -a search_query="Pokemon Base Set PSA 10" -O vintage.json

# High-value cards
scrapy crawl ebay_graded_cards -a search_query="Pokemon PSA 10 1st Edition" -O first_edition.json

# BGS graded cards
scrapy crawl ebay_graded_cards -a search_query="Pokemon BGS 10" -O bgs_10.json
```

## Data Analysis

View scraped data:
```bash
# Pretty print first 5 items
python3 -c "import json; data=json.load(open('output.json')); print(json.dumps(data[:5], indent=2))"

# Count items by grading company
python3 -c "import json; from collections import Counter; data=json.load(open('output.json')); print(Counter(item['grading_company'] for item in data))"

# Average price by grade
python3 -c "import json; from statistics import mean; data=json.load(open('output.json')); grades={}; [grades.setdefault(item['grade'], []).append(item['price']) for item in data if item.get('price')]; print({g:mean(prices) for g, prices in grades.items()})"
```

## Next Steps

1. **Test Mercari Spider**: `scrapy crawl mercari_graded_cards`
2. **Add More Marketplaces**: Expand to TCGPlayer, eBay UK, etc.
3. **Database Integration**: Store data in PostgreSQL/MongoDB
4. **Price Tracking**: Run regularly to track price changes
5. **Image Analysis**: Use CV to verify card condition from images

## Files Modified

- ✅ `graded_cards_scraper/spiders/ebay_spider.py` - Fixed selectors, added item yield logic
- ✅ `graded_cards_scraper/settings.py` - Added anti-bot config, enabled image pipeline
- ✅ `graded_cards_scraper/pipelines.py` - Image download and organization
- ✅ `graded_cards_scraper/items.py` - Data model definition

## Known Issues & Limitations

1. **Card Name Parsing**: Some titles don't have clear card names (returns empty string)
   - These items still have full title and other data
   - Can be parsed manually or with improved regex

2. **Price Variations**: Some listings show price ranges (e.g., "$100 to $500")
   - Currently extracts first price found
   - Consider updating regex to handle ranges

3. **Rate Limiting**: eBay may throttle after extended scraping
   - Increase delays if you see challenges
   - Consider using rotating proxies for large-scale scraping

## Support

For issues or questions:
1. Check this guide first
2. Review Scrapy logs for error messages
3. Test with headless=False to see what's happening
4. Verify eBay page structure hasn't changed
