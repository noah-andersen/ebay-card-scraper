"""
Debug script to test eBay scraping and identify issues.
"""

import requests
from bs4 import BeautifulSoup
import config
import random


def test_ebay_connection():
    """Test basic connection to eBay"""
    print("Testing eBay connection...")
    try:
        headers = {
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        response = requests.get('https://www.ebay.com', headers=headers, timeout=30)
        print(f"✓ Connection successful! Status: {response.status_code}")
        return True
    except requests.exceptions.Timeout:
        print(f"✗ Connection timed out. This could mean:")
        print(f"   - Your internet connection is slow")
        print(f"   - eBay is blocking automated requests")
        print(f"   - Firewall/proxy blocking access")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_search_url():
    """Test if we can build and access a search URL"""
    print("\nTesting search URL construction...")
    
    search_query = "pokemon PSA 10"
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}&_sacat=0"
    print(f"Search URL: {url}")
    
    try:
        headers = {
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        print("  Attempting to fetch search results (this may take 30-60 seconds)...")
        response = requests.get(url, headers=headers, timeout=60)
        print(f"✓ Search page loaded! Status: {response.status_code}")
        
        # Save HTML for inspection
        with open('debug_search_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✓ Saved search page HTML to debug_search_page.html")
        
        return response
    except requests.exceptions.Timeout:
        print(f"✗ Search request timed out after 60 seconds")
        print(f"  Try:")
        print(f"   1. Check your internet connection")
        print(f"   2. Try using a VPN")
        print(f"   3. Access eBay in your browser to verify it's accessible")
        return None
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return None


def analyze_search_results(response):
    """Analyze the HTML structure of search results"""
    print("\nAnalyzing search results HTML structure...")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Try multiple possible selectors for listings
    selectors = [
        ('div.s-item__info', 'div with class s-item__info'),
        ('li.s-item', 'li with class s-item'),
        ('div.s-item', 'div with class s-item'),
        ('li[data-view]', 'li with data-view attribute'),
        ('div[data-view]', 'div with data-view attribute'),
    ]
    
    for selector, description in selectors:
        elements = soup.select(selector)
        print(f"\n  {description}: Found {len(elements)} elements")
        
        if elements:
            print(f"    First element preview:")
            first = elements[0]
            
            # Try to find title
            title_selectors = [
                'div.s-item__title',
                'h3.s-item__title',
                'span.s-item__title',
                '.s-item__title'
            ]
            for ts in title_selectors:
                title = first.select_one(ts)
                if title:
                    print(f"      Title ({ts}): {title.get_text(strip=True)[:60]}...")
                    break
            
            # Try to find image
            img_selectors = [
                'img.s-item__image-img',
                'img[src]',
                '.s-item__image img'
            ]
            for imgs in img_selectors:
                img = first.select_one(imgs)
                if img:
                    print(f"      Image ({imgs}): {img.get('src', 'No src')[:60]}...")
                    break
            
            # Try to find price
            price_selectors = [
                'span.s-item__price',
                '.s-item__price',
                'span[class*="price"]'
            ]
            for ps in price_selectors:
                price = first.select_one(ps)
                if price:
                    print(f"      Price ({ps}): {price.get_text(strip=True)}")
                    break
    
    # Check for "no results" message
    no_results = soup.select_one('h3.srp-save-null-search__heading')
    if no_results:
        print(f"\n⚠️  No results message found: {no_results.get_text(strip=True)}")
    
    # Count total results
    result_count = soup.select_one('h1.srp-controls__count-heading')
    if result_count:
        print(f"\n✓ Results count: {result_count.get_text(strip=True)}")


def test_image_download():
    """Test downloading a sample eBay image"""
    print("\nTesting image download...")
    
    # Use a known working eBay image URL (this is just a placeholder)
    test_url = "https://i.ebayimg.com/images/g/placeholder/s-l500.jpg"
    
    try:
        headers = {
            'User-Agent': random.choice(config.USER_AGENTS),
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"✓ Image download test: Status {response.status_code}")
        print(f"  Content type: {response.headers.get('content-type')}")
        print(f"  Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"✗ Image download failed: {e}")


def main():
    print("="*70)
    print("eBay Scraper Debug Tool")
    print("="*70)
    
    # Test 1: Basic connection
    if not test_ebay_connection():
        print("\n❌ Cannot connect to eBay. Check your internet connection.")
        return
    
    # Test 2: Search URL
    response = test_search_url()
    if not response:
        print("\n❌ Cannot access search page.")
        return
    
    # Test 3: Analyze results
    analyze_search_results(response)
    
    # Test 4: Image download
    test_image_download()
    
    print("\n" + "="*70)
    print("Debug complete! Check debug_search_page.html for the raw HTML.")
    print("="*70)


if __name__ == '__main__':
    main()
