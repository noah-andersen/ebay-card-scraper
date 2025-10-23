# eBay Card Scraper - Project Summary

## ✅ Setup Complete!

Your eBay card scraper is ready to use. Here's what has been created:

### 📁 Project Structure

```
ebay-card-scraper/
├── scraper.py           # Main scraper class with all scraping logic
├── main.py              # Command-line interface
├── config.py            # Configuration (URLs, delays, grades, etc.)
├── utils.py             # Helper functions (stats, deduplication, etc.)
├── example.py           # Interactive examples
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # Full documentation
├── QUICKSTART.md        # Quick start guide
├── .gitignore           # Git ignore rules
├── venv/                # Virtual environment (created)
└── data/                # Output directory (will be created on first run)
    ├── images/          # Downloaded card images
    └── metadata.csv     # Card metadata
```

### 🎯 What It Does

The scraper searches eBay for graded Pokemon cards based on:
- **Grading Company:** PSA, BGS, or CGC
- **Grade:** 1-10 (including half grades like 9.5)
- **Card Name:** Optional specific card (e.g., "Charizard")
- **Sold Listings:** Option to get actual sale prices

For each card found, it:
1. Downloads the card image
2. Saves metadata (grade, price, listing details)
3. Exports everything to organized files

### 🚀 Quick Start Examples

#### 1. Basic Command Line Usage
```bash
# Activate virtual environment first
source venv/bin/activate

# Search for PSA 10 cards (10 results)
python main.py --company PSA --grade 10 --max-results 10

# Search for BGS 9.5 Charizard cards
python main.py --company BGS --grade 9.5 --card-name Charizard --max-results 5

# Search sold CGC 10 listings
python main.py --company CGC --grade 10 --sold-only --max-results 10
```

#### 2. Interactive Examples
```bash
python example.py
# Then choose from menu options
```

#### 3. Python Code
```python
from scraper import EbayScraper

scraper = EbayScraper()
scraper.search_graded_cards(
    grading_company='PSA',
    grade=10,
    max_results=10
)
```

### 📊 Output Files

**Images:** `data/images/PSA_10_Charizard_VMAX_123456789.jpg`
- Named: `{company}_{grade}_{card_name}_{listing_id}.jpg`

**Metadata:** `data/metadata.csv`
```csv
listing_id,card_name,grading_company,grade,price,image_url,image_path,timestamp,sold
123456789,Charizard VMAX,PSA,10,599.99,https://...,./data/images/...,2025-10-23T12:00:00,False
```

### ⚙️ Key Features

✓ **Rate Limiting:** 2-5 second delays between requests
✓ **Resume Support:** Skips already downloaded listings
✓ **Error Handling:** Retries failed downloads
✓ **Logging:** Detailed logs in `scraper.log`
✓ **CSV Export:** Easy data analysis with pandas
✓ **Multiple Companies:** PSA, BGS, CGC support
✓ **Sold Listings:** Get actual sale prices

### 🎨 Customization

Edit `config.py` to change:
- Request delays (avoid rate limiting)
- Image quality and size
- Output directories
- Valid grades for each company
- User agents

### 📝 Common Commands

```bash
# View statistics
python -c "from utils import print_statistics; import config; print_statistics(config.METADATA_FILE)"

# Remove duplicates
python -c "from utils import deduplicate_images; import config; deduplicate_images(config.IMAGES_DIR, config.METADATA_FILE)"

# Search all PSA grades (5 per grade)
python main.py --company PSA --all-grades --max-results-per-grade 5
```

### 💡 Best Practices

1. **Start Small:** Test with `--max-results 5` first
2. **Be Respectful:** Use built-in rate limiting
3. **Check Logs:** Monitor `scraper.log` for issues
4. **Backup Data:** Keep your `data/` folder safe
5. **Use Sold Listings:** For accurate pricing data

### 🔍 Use Cases

- **ML Training:** Collect labeled card images by grade
- **Price Analysis:** Track sold prices across grades
- **Dataset Creation:** Build comprehensive card databases
- **Market Research:** Understand grading trends
- **Automation:** Schedule regular scraping runs

### ⚠️ Important Notes

- **Legal:** For educational/research purposes only
- **Respect ToS:** Follow eBay's Terms of Service
- **Rate Limits:** Don't scrape too aggressively
- **API Alternative:** Consider eBay's official API for production

### 🐛 Troubleshooting

**No images downloaded?**
- Check internet connection
- eBay HTML may have changed
- Try different search terms

**Import errors?**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Rate limited?**
- Increase `REQUEST_DELAY_MIN` in `config.py`
- Wait before retrying

### 📚 Next Steps

1. **Test the scraper:**
   ```bash
   python main.py --company PSA --grade 10 --max-results 5
   ```

2. **Check the output:**
   ```bash
   ls data/images/
   cat data/metadata.csv
   ```

3. **Customize for your needs:**
   - Edit `config.py` for your preferences
   - Modify search parameters
   - Add new functionality

4. **Build your dataset:**
   - Run searches for different grades
   - Combine data from multiple companies
   - Analyze pricing trends

### 🤝 Contributing

Feel free to:
- Add support for more TCGs (Yu-Gi-Oh, MTG)
- Improve image quality filtering
- Add database storage
- Implement multi-threading
- Create visualization tools

---

**Ready to start scraping?**
```bash
source venv/bin/activate
python example.py
```

Enjoy building your graded Pokemon card dataset! 🎴✨
