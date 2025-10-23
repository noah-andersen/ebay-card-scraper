#!/usr/bin/env python3
"""
eBay Card Scraper
A Python module for scraping graded Pokemon card data from eBay.
This scraper searches for graded Pokemon cards based on grading company
and downloads images from the listings.
"""

import os
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote_plus, urlparse
import requests
from bs4 import BeautifulSoup


class EbayCardScraper:
    """Scraper for graded Pokemon cards on eBay."""
    
    # Common grading companies for Pokemon cards
    GRADING_COMPANIES = {
        'PSA': 'PSA',
        'BGS': 'BGS',  # Beckett Grading Services
        'CGC': 'CGC',
        'SGC': 'SGC',
    }
    
    def __init__(self, output_dir: str = "ebay_images"):
        """
        Initialize the eBay card scraper.
        
        Args:
            output_dir: Directory to save downloaded images
        """
        self.output_dir = output_dir
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def search_graded_cards(
        self, 
        grading_company: str, 
        card_name: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for graded Pokemon cards on eBay.
        
        Args:
            grading_company: The grading company (PSA, BGS, CGC, SGC)
            card_name: Optional specific card name to search for
            max_results: Maximum number of listings to retrieve
            
        Returns:
            List of dictionaries containing listing information
        """
        # Validate grading company
        grading_company = grading_company.upper()
        if grading_company not in self.GRADING_COMPANIES:
            raise ValueError(
                f"Invalid grading company. Must be one of: {', '.join(self.GRADING_COMPANIES.keys())}"
            )
        
        # Build search query
        search_terms = f"Pokemon {grading_company}"
        if card_name:
            search_terms = f"{search_terms} {card_name}"
        
        # Build search parameters
        params = {
            '_nkw': search_terms,
            '_sacat': '0',  # All categories
            'LH_TitleDesc': '1',  # Search title and description
            '_sop': '12',  # Sort by: Best Match
        }
        
        search_url = f"{self.base_url}?{urlencode(params)}"
        
        print(f"Searching for: {search_terms}")
        print(f"URL: {search_url}")
        
        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching search results: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        listings = self._parse_listings(soup, max_results)
        
        print(f"Found {len(listings)} listings")
        return listings
    
    def _parse_listings(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """
        Parse eBay search results page.
        
        Args:
            soup: BeautifulSoup object of the search results page
            max_results: Maximum number of listings to parse
            
        Returns:
            List of dictionaries containing listing information
        """
        listings = []
        
        # eBay uses different class names for search results
        # Try multiple selectors to find listings
        items = soup.find_all('div', class_='s-item__info') or \
                soup.find_all('li', class_='s-item') or \
                soup.find_all('div', class_='srp-results')
        
        for item in items[:max_results]:
            try:
                listing_data = {}
                
                # Extract title
                title_elem = item.find('h3', class_='s-item__title') or \
                            item.find('div', class_='s-item__title')
                if title_elem:
                    listing_data['title'] = title_elem.get_text(strip=True)
                
                # Extract URL
                link_elem = item.find('a', class_='s-item__link') or \
                           item.find('a', href=re.compile(r'/itm/'))
                if link_elem and link_elem.get('href'):
                    listing_data['url'] = link_elem['href']
                
                # Extract price
                price_elem = item.find('span', class_='s-item__price')
                if price_elem:
                    listing_data['price'] = price_elem.get_text(strip=True)
                
                # Extract image URL
                img_elem = item.find('img', class_='s-item__image-img') or \
                          item.find('img')
                if img_elem and img_elem.get('src'):
                    listing_data['image_url'] = img_elem['src']
                
                # Only add if we have at least title and image
                if listing_data.get('title') and listing_data.get('image_url'):
                    listings.append(listing_data)
                    
            except Exception as e:
                print(f"Error parsing listing: {e}")
                continue
        
        return listings
    
    def download_listing_images(
        self, 
        listing_url: str, 
        card_name: Optional[str] = None
    ) -> List[str]:
        """
        Download all images from a specific eBay listing.
        
        Args:
            listing_url: URL of the eBay listing
            card_name: Optional name to use for file naming
            
        Returns:
            List of file paths where images were saved
        """
        print(f"Fetching listing: {listing_url}")
        
        try:
            response = self.session.get(listing_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching listing page: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        image_urls = self._extract_listing_images(soup)
        
        if not image_urls:
            print("No images found in listing")
            return []
        
        print(f"Found {len(image_urls)} images")
        
        # Create subdirectory for this listing
        if card_name:
            safe_name = re.sub(r'[^\w\s-]', '', card_name)[:50]
        else:
            # Extract item ID from URL if possible
            item_id_match = re.search(r'/itm/(\d+)', listing_url)
            safe_name = item_id_match.group(1) if item_id_match else 'listing'
        
        listing_dir = os.path.join(self.output_dir, safe_name)
        os.makedirs(listing_dir, exist_ok=True)
        
        # Download images
        saved_files = []
        for idx, img_url in enumerate(image_urls, 1):
            try:
                saved_path = self._download_image(img_url, listing_dir, idx)
                if saved_path:
                    saved_files.append(saved_path)
                    print(f"Downloaded image {idx}/{len(image_urls)}: {saved_path}")
                time.sleep(0.5)  # Be polite to the server
            except Exception as e:
                print(f"Error downloading image {idx}: {e}")
                continue
        
        return saved_files
    
    def _extract_listing_images(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract image URLs from a listing page.
        
        Args:
            soup: BeautifulSoup object of the listing page
            
        Returns:
            List of image URLs
        """
        image_urls = []
        
        # Try to find the image gallery or main product images
        # eBay often stores image URLs in various places
        
        # Method 1: Look for high-resolution images in picture panel
        img_elements = soup.find_all('img', class_=re.compile(r'(img|image|picture)'))
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src and self._is_valid_image_url(src):
                # Try to get higher resolution version
                high_res_url = self._get_high_res_url(src)
                if high_res_url not in image_urls:
                    image_urls.append(high_res_url)
        
        # Method 2: Look in the photo gallery thumbnails
        thumbnails = soup.find_all('button', class_=re.compile(r'(thumb|thumbnail)'))
        for thumb in thumbnails:
            img = thumb.find('img')
            if img:
                src = img.get('src') or img.get('data-src')
                if src and self._is_valid_image_url(src):
                    high_res_url = self._get_high_res_url(src)
                    if high_res_url not in image_urls:
                        image_urls.append(high_res_url)
        
        return image_urls
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL."""
        if not url or url.startswith('data:'):
            return False
        
        # Parse the URL to properly check the domain
        try:
            parsed = urlparse(url)
            # Check if domain is from eBay's image server
            if parsed.netloc:
                # Only accept if the actual domain is ebayimg.com or a subdomain (e.g., i.ebayimg.com)
                # This prevents attacks like https://evil.com/ebayimg.com/fake.jpg
                # or https://evilebayimg.com/fake.jpg
                if parsed.netloc == 'ebayimg.com' or parsed.netloc.endswith('.ebayimg.com'):
                    return True
                # For other domains, check if it's a valid image extension
                # but be strict - only accept if it's a proper image URL
                if url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    return True
        except Exception:
            pass
        
        return False
    
    def _get_high_res_url(self, url: str) -> str:
        """
        Convert thumbnail URL to high-resolution version if possible.
        
        Args:
            url: Original image URL
            
        Returns:
            High-resolution image URL
        """
        # eBay images often have size parameters that can be modified
        # s-l64.jpg -> s-l1600.jpg for higher resolution
        url = url.replace('s-l64.', 's-l1600.')
        url = url.replace('s-l140.', 's-l1600.')
        url = url.replace('s-l225.', 's-l1600.')
        url = url.replace('s-l300.', 's-l1600.')
        url = url.replace('s-l500.', 's-l1600.')
        return url
    
    def _download_image(self, url: str, output_dir: str, index: int) -> Optional[str]:
        """
        Download an image from URL.
        
        Args:
            url: Image URL
            output_dir: Directory to save the image
            index: Index for filename
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('Content-Type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'gif' in content_type:
                ext = 'gif'
            else:
                # Try to get extension from URL
                ext = url.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                    ext = 'jpg'
            
            filename = f"image_{index:03d}.{ext}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def scrape_and_download(
        self,
        grading_company: str,
        card_name: Optional[str] = None,
        max_listings: int = 5
    ) -> Dict:
        """
        Search for graded cards and download images from listings.
        
        Args:
            grading_company: The grading company (PSA, BGS, CGC, SGC)
            card_name: Optional specific card name to search for
            max_listings: Maximum number of listings to process
            
        Returns:
            Dictionary with results summary
        """
        results = {
            'search_query': f"Pokemon {grading_company}" + (f" {card_name}" if card_name else ""),
            'listings_found': 0,
            'listings_downloaded': 0,
            'total_images': 0,
            'details': []
        }
        
        # Search for listings
        listings = self.search_graded_cards(grading_company, card_name, max_listings)
        results['listings_found'] = len(listings)
        
        # Download images from each listing
        for listing in listings:
            if listing.get('url'):
                print(f"\nProcessing: {listing.get('title', 'Unknown')}")
                saved_files = self.download_listing_images(
                    listing['url'],
                    listing.get('title')
                )
                
                if saved_files:
                    results['listings_downloaded'] += 1
                    results['total_images'] += len(saved_files)
                    results['details'].append({
                        'title': listing.get('title'),
                        'url': listing.get('url'),
                        'price': listing.get('price'),
                        'images_saved': len(saved_files),
                        'files': saved_files
                    })
                
                time.sleep(1)  # Be polite between requests
        
        return results


def main():
    """Example usage of the eBay card scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape graded Pokemon card images from eBay'
    )
    parser.add_argument(
        'grading_company',
        type=str,
        help='Grading company (PSA, BGS, CGC, or SGC)'
    )
    parser.add_argument(
        '--card',
        type=str,
        help='Specific card name to search for (optional)',
        default=None
    )
    parser.add_argument(
        '--max-listings',
        type=int,
        help='Maximum number of listings to process (default: 5)',
        default=5
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save images (default: ebay_images)',
        default='ebay_images'
    )
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = EbayCardScraper(output_dir=args.output_dir)
    
    # Run scraping
    print(f"\n{'='*60}")
    print(f"eBay Graded Pokemon Card Scraper")
    print(f"{'='*60}\n")
    
    results = scraper.scrape_and_download(
        grading_company=args.grading_company,
        card_name=args.card,
        max_listings=args.max_listings
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Scraping Complete!")
    print(f"{'='*60}")
    print(f"Search Query: {results['search_query']}")
    print(f"Listings Found: {results['listings_found']}")
    print(f"Listings Downloaded: {results['listings_downloaded']}")
    print(f"Total Images Saved: {results['total_images']}")
    print(f"Output Directory: {args.output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
