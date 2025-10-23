"""
eBay marketplace scraper for graded Pokemon cards (refactored).
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from typing import Optional, Dict
from datetime import datetime
import re

from scrapers.base_scraper import BaseScraper
import config


class EbayScraper(BaseScraper):
    """Scraper for eBay marketplace"""
    
    BASE_URL = "https://www.ebay.com/sch/i.html"
    SOLD_BASE_URL = "https://www.ebay.com/sch/i.html?LH_Sold=1&LH_Complete=1"
    
    def __init__(self, output_dir: str = None):
        super().__init__('ebay', output_dir)
        self.logger.info("eBay scraper initialized")
    
    def _build_search_url(self, grading_company: str, grade: float, card_name: str = None, 
                         sold_only: bool = False) -> str:
        """
        Build eBay search URL with parameters.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade (1-10)
            card_name: Optional specific card name to search
            sold_only: Whether to search only sold listings
            
        Returns:
            Complete eBay search URL
        """
        # Build search query
        query_parts = ['pokemon', grading_company, str(int(grade) if grade == int(grade) else grade)]
        if card_name:
            query_parts.insert(1, card_name)
        
        search_query = ' '.join(query_parts)
        
        # Build URL parameters
        params = {
            '_nkw': search_query,
            '_sacat': '0',  # All categories
            'LH_TitleDesc': '0',  # Title only
            '_sop': '12',  # Sort by: newly listed
        }
        
        if sold_only:
            params['LH_Sold'] = '1'
            params['LH_Complete'] = '1'
        
        base_url = self.SOLD_BASE_URL if sold_only else self.BASE_URL
        url = f"{base_url.split('?')[0]}?{urlencode(params)}"
        
        return url
    
    def _extract_listing_data(self, listing_soup) -> Optional[Dict]:
        """
        Extract data from a single listing element.
        
        Args:
            listing_soup: BeautifulSoup element for a listing
            
        Returns:
            Dictionary with listing data or None if extraction fails
        """
        try:
            # Extract listing ID
            listing_id = listing_soup.get('data-view') or listing_soup.get('listingid')
            if not listing_id:
                # Try to extract from link
                link = listing_soup.find('a', class_='s-item__link')
                if link and link.get('href'):
                    match = re.search(r'/itm/(\d+)', link.get('href'))
                    if match:
                        listing_id = match.group(1)
            
            # Extract title
            title_elem = listing_soup.find('div', class_='s-item__title') or \
                        listing_soup.find('h3', class_='s-item__title')
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Skip "Shop on eBay" and similar
            if "Shop on eBay" in title or not title or title == "Unknown":
                return None
            
            # Extract price
            price_elem = listing_soup.find('span', class_='s-item__price')
            price_text = price_elem.get_text(strip=True) if price_elem else '0'
            # Clean price text
            price = re.sub(r'[^\d.]', '', price_text.split('to')[0])
            
            # Extract image URL
            img_elem = listing_soup.find('img', class_='s-item__image-img')
            img_url = img_elem.get('src') if img_elem else None
            
            # Skip if no image
            if not img_url or 'thumbs' in img_url:
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
        Search eBay for graded Pokemon cards and save images.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade (1-10)
            card_name: Optional specific card name
            max_results: Maximum number of results to scrape
            sold_only: Whether to search only sold listings
            
        Returns:
            Number of images successfully downloaded
        """
        # Validate inputs
        grading_company = grading_company.upper()
        if grading_company not in config.GRADING_COMPANIES:
            raise ValueError(f"Invalid grading company. Must be one of: {list(config.GRADING_COMPANIES.keys())}")
        
        self.logger.info(f"Starting eBay search for {grading_company} {grade} Pokemon cards" + 
                        (f" - {card_name}" if card_name else ""))
        
        url = self._build_search_url(grading_company, grade, card_name, sold_only)
        self.logger.info(f"Search URL: {url}")
        
        downloaded_count = 0
        page = 1
        
        while downloaded_count < max_results:
            try:
                # Add page parameter for pagination
                page_url = f"{url}&_pgn={page}"
                
                self.logger.info(f"Fetching page {page}...")
                response = requests.get(page_url, headers=self._get_headers(), 
                                       timeout=config.TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all listing items
                listings = soup.find_all('div', class_='s-item__info') or \
                          soup.find_all('li', class_='s-item')
                
                if not listings:
                    self.logger.warning(f"No listings found on page {page}")
                    # Save HTML for debugging
                    if page == 1:
                        with open('ebay_debug.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        self.logger.info("Saved page HTML to ebay_debug.html for inspection")
                    break
                
                self.logger.info(f"Found {len(listings)} listings on page {page}")
                
                for listing in listings:
                    if downloaded_count >= max_results:
                        break
                    
                    # Extract listing data
                    listing_data = self._extract_listing_data(listing)
                    if not listing_data:
                        continue
                    
                    # Create filename
                    card_title = self._sanitize_filename(listing_data['title'])
                    filename = f"{grading_company}_{grade}_{card_title}_{listing_data['listing_id']}.{config.IMAGE_FORMAT}"
                    
                    # Check if already downloaded
                    if any(m.get('listing_id') == listing_data['listing_id'] for m in self.metadata):
                        self.logger.info(f"Skipping already downloaded listing: {listing_data['listing_id']}")
                        continue
                    
                    # Download image
                    filepath = self._download_image(listing_data['image_url'], filename)
                    
                    if filepath:
                        # Add to metadata
                        self.metadata.append({
                            'marketplace': 'ebay',
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
                
                # Move to next page
                page += 1
                
                # Delay between pages
                time.sleep(random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX))
                
            except Exception as e:
                self.logger.error(f"Error on page {page}: {e}")
                break
        
        # Save metadata
        self._save_metadata()
        
        self.logger.info(f"Completed! Downloaded {downloaded_count} images from eBay")
        return downloaded_count


if __name__ == '__main__':
    # Test the scraper
    print("Testing eBay scraper...\n")
    
    scraper = EbayScraper()
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=10,
        max_results=5
    )
    
    print(f"\nTest complete! Downloaded {count} images from eBay")
