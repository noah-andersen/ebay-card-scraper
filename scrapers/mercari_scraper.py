"""
Mercari marketplace scraper for graded Pokemon cards.
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Optional, Dict
from datetime import datetime
import re
import json

from scrapers.base_scraper import BaseScraper
import config


class MercariScraper(BaseScraper):
    """Scraper for Mercari marketplace"""
    
    BASE_URL = "https://www.mercari.com"
    SEARCH_URL = "https://www.mercari.com/search/"
    API_URL = "https://www.mercari.com/v1/api"
    
    def __init__(self, output_dir: str = None):
        super().__init__('mercari', output_dir)
        self.session = requests.Session()
        self.logger.info("Mercari scraper initialized")
    
    def _get_enhanced_headers(self):
        """Get enhanced headers specifically for Mercari"""
        headers = self._get_headers()
        # Add Mercari-specific headers
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.mercari.com/'
        })
        return headers
    
    def _build_search_url(self, grading_company: str, grade: float, 
                         card_name: str = None) -> str:
        """
        Build Mercari search URL.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade
            card_name: Optional card name
            
        Returns:
            Mercari search URL
        """
        query_parts = ['graded', 'pokemon', grading_company, str(int(grade) if grade == int(grade) else grade)]
        if card_name:
            query_parts.insert(2, card_name)
        
        search_query = ' '.join(query_parts)
        
        params = {
            'keyword': search_query,
            'status': 'on_sale',  # Only show items for sale
            'sort': 'created_time:desc'
        }
        
        return f"{self.SEARCH_URL}?{urlencode(params)}"
    
    def _extract_listing_data(self, item_soup) -> Optional[Dict]:
        """
        Extract data from a single Mercari listing.
        
        Args:
            item_soup: BeautifulSoup element for a listing
            
        Returns:
            Dictionary with listing data or None if extraction fails
        """
        try:
            # Extract listing ID
            listing_id = item_soup.get('data-id') or item_soup.get('id', '')
            
            # Try to find link with item ID
            link = item_soup.find('a', href=re.compile(r'/us/item/'))
            if link:
                href = link.get('href', '')
                id_match = re.search(r'/item/([a-zA-Z0-9]+)', href)
                if id_match:
                    listing_id = id_match.group(1)
            
            # Extract title
            title_elem = item_soup.find('span', {'data-testid': 'ItemName'}) or \
                        item_soup.find('div', class_=re.compile(r'.*itemName.*', re.I)) or \
                        item_soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Extract price
            price_elem = item_soup.find('span', {'data-testid': 'ItemPrice'}) or \
                        item_soup.find('div', class_=re.compile(r'.*price.*', re.I))
            price_text = price_elem.get_text(strip=True) if price_elem else '$0'
            price = re.sub(r'[^\d.]', '', price_text)
            
            # Extract image URL
            img_elem = item_soup.find('img', {'data-testid': 'ItemThumbnail'}) or \
                      item_soup.find('img', src=re.compile(r'mercari|image'))
            
            img_url = None
            if img_elem:
                img_url = img_elem.get('src') or img_elem.get('data-src')
            
            # Skip if no image
            if not img_url:
                return None
            
            return {
                'listing_id': listing_id or 'unknown',
                'title': title,
                'price': price,
                'image_url': img_url
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting listing data: {e}")
            return None
    
    def search_graded_cards(self, grading_company: str, grade: float, 
                           card_name: str = None, max_results: int = 50,
                           sold_only: bool = False) -> int:
        """
        Search Mercari for graded Pokemon cards.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade (1-10)
            card_name: Optional specific card name
            max_results: Maximum number of results to scrape
            sold_only: Whether to search only sold listings
            
        Returns:
            Number of images successfully downloaded
        """
        grading_company = grading_company.upper()
        if grading_company not in config.GRADING_COMPANIES:
            raise ValueError(f"Invalid grading company. Must be one of: {list(config.GRADING_COMPANIES.keys())}")
        
        self.logger.info(f"Starting Mercari search for {grading_company} {grade} Pokemon cards" + 
                        (f" - {card_name}" if card_name else ""))
        
        url = self._build_search_url(grading_company, grade, card_name)
        self.logger.info(f"Search URL: {url}")
        
        downloaded_count = 0
        page = 1
        
        try:
            self.logger.info(f"Fetching page {page}...")
            
            # Use enhanced headers and session
            response = self.session.get(
                url, 
                headers=self._get_enhanced_headers(),
                timeout=config.TIMEOUT,
                allow_redirects=True
            )
            
            # Check for blocking
            if response.status_code == 403:
                self.logger.error("❌ Mercari blocked the request (403 Forbidden)")
                self.logger.info("\n⚠️  MERCARI BOT DETECTION ACTIVE ⚠️")
                self.logger.info("Mercari has strong anti-scraping measures. Here are your options:")
                self.logger.info("\n1. 🌐 Use Selenium/Playwright for browser automation")
                self.logger.info("2. 📱 Try Mercari mobile app or website manually")
                self.logger.info("3. 🔑 Check if Mercari offers an official API")
                self.logger.info("4. ⏱️  Add longer delays between requests")
                self.logger.info("5. 🔄 Use rotating proxies\n")
                return 0
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Mercari uses various selectors - try multiple approaches
            listing_selectors = [
                'div[data-testid="SearchResults"] > div',
                'li[data-testid="SearchResult"]',
                'div[itemtype="http://schema.org/Product"]',
                'div.sc-*[data-id]',  # Styled components
            ]
            
            listings = []
            for selector in listing_selectors:
                found = soup.select(selector)
                if found:
                    listings = found
                    self.logger.info(f"Found {len(listings)} listings using selector: {selector}")
                    break
            
            # If no listings found with selectors, try finding all links to items
            if not listings:
                item_links = soup.find_all('a', href=re.compile(r'/us/item/'))
                if item_links:
                    listings = [link.parent.parent for link in item_links[:max_results]]
                    self.logger.info(f"Found {len(listings)} item links")
            
            if not listings:
                self.logger.warning("No listings found on page")
                # Save the HTML for debugging
                with open('mercari_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.info("Saved page HTML to mercari_debug.html for inspection")
                return 0
            
            for listing in listings[:max_results]:
                if downloaded_count >= max_results:
                    break
                
                # Extract listing data
                listing_data = self._extract_listing_data(listing)
                if not listing_data:
                    continue
                
                # Check if already downloaded
                if any(m.get('listing_id') == listing_data['listing_id'] for m in self.metadata):
                    self.logger.info(f"Skipping already downloaded listing: {listing_data['listing_id']}")
                    continue
                
                # Create filename
                card_title = self._sanitize_filename(listing_data['title'])
                filename = f"{grading_company}_{grade}_{card_title}_{listing_data['listing_id']}.{config.IMAGE_FORMAT}"
                
                # Download image
                filepath = self._download_image(listing_data['image_url'], filename)
                
                if filepath:
                    # Add to metadata
                    self.metadata.append({
                        'marketplace': 'mercari',
                        'listing_id': listing_data['listing_id'],
                        'card_name': listing_data['title'],
                        'grading_company': grading_company,
                        'grade': grade,
                        'price': listing_data['price'],
                        'image_url': listing_data['image_url'],
                        'image_path': filepath,
                        'timestamp': datetime.now().isoformat(),
                        'sold': sold_only
                    })
                    
                    downloaded_count += 1
                    self.logger.info(f"Progress: {downloaded_count}/{max_results}")
                
                # Rate limiting
                time.sleep(random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX))
            
            # Save metadata
            self._save_metadata()
            
            self.logger.info(f"Completed! Downloaded {downloaded_count} images from Mercari")
            return downloaded_count
            
        except Exception as e:
            self.logger.error(f"Error during Mercari scraping: {e}")
            return downloaded_count


if __name__ == '__main__':
    # Test the scraper
    print("Testing Mercari scraper...\n")
    
    scraper = MercariScraper()
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=10,
        max_results=5
    )
    
    print(f"\nTest complete! Downloaded {count} images from Mercari")
