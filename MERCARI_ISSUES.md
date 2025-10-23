# Mercari Scraper - Known Issues and Solutions

## Issue: 403 Forbidden Error

**Problem:** Mercari returns a 403 Forbidden error when scraping.

```
ERROR - Error during Mercari scraping: 403 Client Error: Forbidden
```

### Why This Happens

Mercari has **strong anti-bot protection** that detects and blocks automated requests. This is more aggressive than eBay's protection.

### Solutions

#### Option 1: Use Selenium (Recommended)

Install Selenium to use a real browser:

```bash
pip install selenium webdriver-manager
```

Create `scrapers/mercari_selenium_scraper.py`:

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class MercariSeleniumScraper:
    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
    
    def search(self, query):
        url = f"https://www.mercari.com/search/?keyword={query}"
        self.driver.get(url)
        time.sleep(3)  # Wait for JavaScript to load
        
        # Extract items
        items = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="SearchResult"]')
        return items
    
    def close(self):
        self.driver.quit()
```

Usage:
```python
scraper = MercariSeleniumScraper(headless=False)
items = scraper.search("graded pokemon PSA 10")
scraper.close()
```

#### Option 2: Use Playwright (Modern Alternative)

```bash
pip install playwright
playwright install
```

```python
from playwright.sync_api import sync_playwright

def scrape_mercari(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.mercari.com/search/?keyword={query}")
        page.wait_for_timeout(2000)
        
        # Extract data
        items = page.query_selector_all('[data-testid="SearchResult"]')
        
        browser.close()
        return items
```

#### Option 3: Manual Collection

Since Mercari blocks automation:
1. Visit https://www.mercari.com/search/
2. Search for "graded pokemon PSA 10"
3. Manually save images you need
4. Use this data for your project

#### Option 4: Use Rotating Proxies

If you need automation at scale:
1. Use a proxy service (ScraperAPI, Bright Data, etc.)
2. Rotate user agents
3. Add random delays
4. Respect rate limits

```python
import requests

proxies = {
    'http': 'http://scraperapi:[email protected]:8001',
    'https': 'http://scraperapi:[email protected]:8001'
}

response = requests.get(url, proxies=proxies)
```

#### Option 5: Check for Official API

Check if Mercari offers:
- Official API for developers
- Partner program
- Data access options

## Alternative: Focus on eBay

Since eBay has better (though still limited) scraping tolerance:
1. Collect more data from eBay
2. Use eBay's official API
3. Consider other marketplaces:
   - TCGPlayer
   - PWCC Marketplace
   - eBay sold listings

## Best Practices

If you must scrape Mercari:
- ✅ Use Selenium/Playwright
- ✅ Add 5-10 second delays between requests
- ✅ Scrape during off-peak hours
- ✅ Keep request volume low (< 100 per day)
- ✅ Rotate user agents
- ✅ Use residential proxies
- ❌ Don't use multiple threads
- ❌ Don't scrape excessively

## Legal Considerations

- Review Mercari's Terms of Service
- Respect robots.txt
- Consider reaching out to Mercari for data access
- Use data responsibly and ethically

## Summary

**TL;DR:** Mercari blocks basic HTTP requests. Use Selenium or Playwright for automated scraping, or collect data manually. For production use, seek official API access or use alternative marketplaces.
