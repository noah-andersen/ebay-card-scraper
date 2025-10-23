"""
Alternative eBay scraper using Selenium for better compatibility.
Use this if the requests-based scraper is being blocked.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import requests
from PIL import Image
from io import BytesIO
import pandas as pd
from datetime import datetime
import re

import config


class EbaySeleniumScraper:
    """
    eBay scraper using Selenium WebDriver for better compatibility.
    """
    
    def __init__(self, headless=True, output_dir=None):
        """
        Initialize Selenium scraper.
        
        Args:
            headless: Run browser in headless mode (no GUI)
            output_dir: Directory to save images and metadata
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.images_dir = os.path.join(self.output_dir, 'images')
        self.metadata_file = os.path.join(self.output_dir, 'metadata_selenium.csv')
        
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.metadata = []
        self.headless = headless
        self.driver = None
        
        print(f"Selenium scraper initialized")
        print(f"Output directory: {self.output_dir}")
        print(f"Headless mode: {headless}")
    
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if self.driver:
            return
        
        print("Initializing Chrome WebDriver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={config.USER_AGENTS[0]}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✓ WebDriver initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize WebDriver: {e}")
            print("\nMake sure Chrome and ChromeDriver are installed:")
            print("  brew install --cask google-chrome")
            print("  brew install chromedriver")
            raise
    
    def search_graded_cards(self, grading_company, grade, card_name=None, 
                           max_results=20, sold_only=False):
        """
        Search for graded cards using Selenium.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade
            card_name: Optional card name
            max_results: Maximum results to scrape
            sold_only: Search sold listings only
            
        Returns:
            Number of images downloaded
        """
        self._init_driver()
        
        # Build search query
        query_parts = ['pokemon', grading_company, str(grade)]
        if card_name:
            query_parts.insert(1, card_name)
        search_query = ' '.join(query_parts)
        
        # Build URL
        base_url = "https://www.ebay.com/sch/i.html"
        params = f"?_nkw={search_query.replace(' ', '+')}&_sacat=0"
        if sold_only:
            params += "&LH_Sold=1&LH_Complete=1"
        
        url = base_url + params
        
        print(f"\nSearching: {search_query}")
        print(f"URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Wait for search results
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "s-item"))
                )
            except TimeoutException:
                print("✗ No search results found or page took too long to load")
                return 0
            
            downloaded_count = 0
            page = 1
            
            while downloaded_count < max_results:
                print(f"\nProcessing page {page}...")
                
                # Find all listings
                listings = self.driver.find_elements(By.CLASS_NAME, "s-item")
                print(f"Found {len(listings)} listings on page {page}")
                
                if not listings:
                    print("No more listings found")
                    break
                
                for listing in listings:
                    if downloaded_count >= max_results:
                        break
                    
                    try:
                        # Extract title
                        try:
                            title_elem = listing.find_element(By.CLASS_NAME, "s-item__title")
                            title = title_elem.text
                        except:
                            continue
                        
                        # Skip sponsored/shop listings
                        if "Shop on eBay" in title or not title:
                            continue
                        
                        # Extract price
                        try:
                            price_elem = listing.find_element(By.CLASS_NAME, "s-item__price")
                            price_text = price_elem.text
                            price = re.sub(r'[^\d.]', '', price_text.split('to')[0])
                        except:
                            price = "0"
                        
                        # Extract image
                        try:
                            img_elem = listing.find_element(By.CSS_SELECTOR, "img.s-item__image-img")
                            img_url = img_elem.get_attribute("src")
                        except:
                            continue
                        
                        # Skip placeholder images
                        if not img_url or 'thumbs' in img_url:
                            continue
                        
                        # Extract listing ID from href
                        try:
                            link_elem = listing.find_element(By.CLASS_NAME, "s-item__link")
                            href = link_elem.get_attribute("href")
                            match = re.search(r'/itm/(\d+)', href)
                            listing_id = match.group(1) if match else f"unknown_{downloaded_count}"
                        except:
                            listing_id = f"unknown_{downloaded_count}"
                        
                        # Check if already downloaded
                        if any(m.get('listing_id') == listing_id for m in self.metadata):
                            continue
                        
                        # Download image
                        card_title = self._sanitize_filename(title)
                        filename = f"{grading_company}_{grade}_{card_title}_{listing_id}.jpg"
                        filepath = self._download_image(img_url, filename)
                        
                        if filepath:
                            self.metadata.append({
                                'listing_id': listing_id,
                                'card_name': title,
                                'grading_company': grading_company,
                                'grade': grade,
                                'price': price,
                                'image_url': img_url,
                                'image_path': filepath,
                                'timestamp': datetime.now().isoformat(),
                                'sold': sold_only
                            })
                            
                            downloaded_count += 1
                            print(f"  [{downloaded_count}/{max_results}] Downloaded: {title[:50]}...")
                        
                        time.sleep(1)  # Small delay between items
                        
                    except Exception as e:
                        print(f"  Error processing listing: {e}")
                        continue
                
                # Try to go to next page
                if downloaded_count < max_results:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "a.pagination__next")
                        next_button.click()
                        time.sleep(3)
                        page += 1
                    except:
                        print("No more pages available")
                        break
            
            # Save metadata
            self._save_metadata()
            
            print(f"\n✓ Downloaded {downloaded_count} images")
            return downloaded_count
            
        except Exception as e:
            print(f"✗ Error during scraping: {e}")
            return 0
    
    def _download_image(self, image_url, filename):
        """Download image from URL"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            filepath = os.path.join(self.images_dir, filename)
            img.save(filepath, 'JPEG', quality=95)
            
            return filepath
        except Exception as e:
            print(f"  Error downloading image: {e}")
            return None
    
    def _sanitize_filename(self, text):
        """Remove invalid characters from filename"""
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')[:50]
    
    def _save_metadata(self):
        """Save metadata to CSV"""
        try:
            df = pd.DataFrame(self.metadata)
            df.to_csv(self.metadata_file, index=False)
            print(f"✓ Saved metadata to {self.metadata_file}")
        except Exception as e:
            print(f"✗ Error saving metadata: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")


if __name__ == '__main__':
    print("Testing Selenium scraper...\n")
    
    scraper = EbaySeleniumScraper(headless=False)  # Set to True to hide browser
    
    try:
        count = scraper.search_graded_cards(
            grading_company='PSA',
            grade=10,
            max_results=5
        )
        print(f"\nTest complete! Downloaded {count} images")
    finally:
        scraper.close()
