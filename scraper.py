import os
import time
import random
import requests
import logging
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import re

import config


class EbayScraper:
    """
    A scraper for collecting graded Pokemon card images and metadata from eBay.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the eBay scraper.
        
        Args:
            output_dir: Directory to save images and metadata (default: config.OUTPUT_DIR)
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.images_dir = os.path.join(self.output_dir, 'images')
        self.metadata_file = os.path.join(self.output_dir, 'metadata.csv')
        
        # Create output directories
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize metadata storage
        self.metadata = []
        
        # Load existing metadata if available
        if os.path.exists(self.metadata_file):
            try:
                existing_df = pd.read_csv(self.metadata_file)
                self.metadata = existing_df.to_dict('records')
                self.logger.info(f"Loaded {len(self.metadata)} existing records")
            except Exception as e:
                self.logger.warning(f"Could not load existing metadata: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get random user agent headers for requests."""
        return {
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
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
        query_parts = ['pokemon', grading_company, str(grade)]
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
        
        base_url = config.EBAY_SOLD_BASE_URL if sold_only else config.EBAY_BASE_URL
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
    
    def _download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        Download and save an image from URL.
        
        Args:
            image_url: URL of the image
            filename: Filename to save the image as
            
        Returns:
            Path to saved image or None if download fails
        """
        try:
            response = requests.get(image_url, headers=self._get_headers(), 
                                   timeout=config.TIMEOUT)
            response.raise_for_status()
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > config.MAX_IMAGE_SIZE[0] or img.size[1] > config.MAX_IMAGE_SIZE[1]:
                img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save image
            filepath = os.path.join(self.images_dir, filename)
            img.save(filepath, config.IMAGE_FORMAT, quality=config.IMAGE_QUALITY)
            
            self.logger.info(f"Saved image: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error downloading image from {image_url}: {e}")
            return None
    
    def _sanitize_filename(self, text: str) -> str:
        """Remove invalid characters from filename."""
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')[:50]
    
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
        
        self.logger.info(f"Starting search for {grading_company} {grade} Pokemon cards" + 
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
        
        self.logger.info(f"Completed! Downloaded {downloaded_count} images")
        return downloaded_count
    
    def _save_metadata(self):
        """Save metadata to CSV file."""
        try:
            df = pd.DataFrame(self.metadata)
            df.to_csv(self.metadata_file, index=False)
            self.logger.info(f"Saved metadata to {self.metadata_file}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
    
    def search_all_grades(self, grading_company: str, card_name: str = None,
                         max_results_per_grade: int = 20, sold_only: bool = False):
        """
        Search for all grades of a grading company.
        
        Args:
            grading_company: PSA, BGS, or CGC
            card_name: Optional specific card name
            max_results_per_grade: Max results per grade level
            sold_only: Whether to search only sold listings
        """
        grading_company = grading_company.upper()
        
        if grading_company == 'PSA':
            grades = config.PSA_GRADES
        elif grading_company in ['BGS', 'BECKETT']:
            grades = config.BGS_GRADES
        elif grading_company == 'CGC':
            grades = config.CGC_GRADES
        else:
            raise ValueError(f"Unknown grading company: {grading_company}")
        
        total_downloaded = 0
        for grade in grades:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Searching for {grading_company} {grade} cards")
            self.logger.info(f"{'='*60}\n")
            
            count = self.search_graded_cards(
                grading_company=grading_company,
                grade=grade,
                card_name=card_name,
                max_results=max_results_per_grade,
                sold_only=sold_only
            )
            total_downloaded += count
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Total images downloaded: {total_downloaded}")
        self.logger.info(f"{'='*60}\n")
