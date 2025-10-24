import scrapy
from scrapy_playwright.page import PageMethod
from graded_cards_scraper.items import GradedCardItem
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MercariGradedCardsSpider(scrapy.Spider):
    name = "mercari_graded_cards"
    allowed_domains = ["mercari.com", "mercdn.net"]  # Include CDN domain for images
    
    def __init__(self, search_query="PSA 10 Pokemon Card", max_pages=5, *args, **kwargs):
        super(MercariGradedCardsSpider, self).__init__(*args, **kwargs)
        self.search_query = search_query
        self.max_pages = int(max_pages)
        self.page_count = 0
        self.items_processed = 0  # Track number of items processed
    
    def start_requests(self):
        """Start scraping from Mercari search results"""
        search_url = f"https://www.mercari.com/search/?keyword={self.search_query.replace(' ', '%20')}"
        
        yield scrapy.Request(
            url=search_url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 3000),
                    PageMethod("wait_for_selector", "[data-testid='SearchResults']", timeout=10000),
                ],
            },
            callback=self.parse_search_results,
        )
    
    def parse_search_results(self, response):
        """Parse search results page and extract card listings"""
        # Mercari uses a lot of JavaScript, so we need to handle it carefully
        listings = response.css('[data-testid="SearchResults"] > div')
        
        self.logger.info(f"Found {len(listings)} listings on page {self.page_count + 1}")
        
        for i, listing in enumerate(listings):
            # Check if we've hit the item limit (if CLOSESPIDER_ITEMCOUNT is set)
            closespider_itemcount = self.crawler.settings.getint('CLOSESPIDER_ITEMCOUNT', 0)
            if closespider_itemcount > 0 and self.items_processed >= closespider_itemcount:
                self.logger.info(f"Reached item limit ({closespider_itemcount}), stopping processing")
                break
            
            # Extract listing link
            link_element = listing.css('a::attr(href)').get()
            if not link_element:
                continue
            
            listing_url = response.urljoin(link_element)
            
            # Extract title
            title = listing.css('[data-testid="ItemName"]::text').get()
            if not title:
                title = listing.css('span::text').get()
            
            # Extract price
            price = listing.css('[data-testid="ItemPrice"]::text').get()
            
            # Extract image and convert to high-resolution
            image_url = listing.css('img::attr(src)').get()
            if image_url:
                # Mercari uses cloudinary CDN with transformation parameters
                # Replace thumbnail transformations with high-res parameters
                # Example: /c_fill,f_auto,fl_progressive:steep,h_190,q_60,w_190/
                # Replace with larger dimensions and better quality
                # Remove size restrictions and set to high quality
                high_res_url = re.sub(r'/c_fill,[^/]+/', '/c_fit,f_auto,fl_progressive:steep,h_1600,q_95,w_1600/', image_url)
                # Also handle other common patterns
                high_res_url = re.sub(r'/w_\d+,h_\d+/', '/w_1600,h_1600/', high_res_url)
                high_res_url = re.sub(r'/q_\d+/', '/q_95/', high_res_url)
                image_url = high_res_url
                self.logger.debug(f"High-res image URL: {image_url}")
            
            # Debug logging
            self.logger.info(f"Item {i}: title={title}, price={price}, url={listing_url is not None}")
            
            if not title or not listing_url:
                self.logger.warning(f"Skipping item {i}: missing title or URL")
                continue
            
            # Increment counter when we process a listing
            self.items_processed += 1
            
            # Parse grading information from title
            grading_info = self.extract_grading_info(title)
            
            # Extract listing ID from URL
            listing_id = None
            if listing_url:
                # Mercari URLs typically like /item/m12345678
                id_match = re.search(r'/item/(m\d+)', listing_url)
                if id_match:
                    listing_id = id_match.group(1)
            
            # Create temporary item with basic info to pass to detail page
            item = GradedCardItem()
            item['title'] = title.strip()
            item['card_name'] = grading_info['card_name']
            item['grading_company'] = grading_info['grading_company']
            item['grade'] = grading_info['grade']
            item['price'] = price.strip() if price else None
            item['listing_url'] = listing_url
            item['listing_id'] = listing_id
            item['image_urls'] = [image_url] if image_url else []  # Thumbnail as fallback
            item['source'] = 'mercari'
            item['scraped_date'] = datetime.now().isoformat()
            
            # Follow listing URL to get all images
            if listing_url:
                self.logger.info(f"Following listing for all images: {item['card_name']}")
                yield response.follow(
                    listing_url,
                    callback=self.parse_listing_details,
                    meta={
                        'item': item,
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod("wait_for_timeout", 2000),
                            PageMethod("wait_for_selector", "img", timeout=10000),
                        ],
                    },
                    dont_filter=True
                )
            else:
                # No URL available, yield item with thumbnail only
                self.logger.info(f"Yielding item (no detail page): {item['card_name']}")
                # No URL available, yield item with thumbnail only
                self.logger.info(f"Yielding item (no detail page): {item['card_name']}")
                yield item
        
        # Handle pagination
        self.page_count += 1
        if self.page_count < self.max_pages:
            # Try to find next page button
            next_button = response.css('[data-testid="pagination-next-button"]::attr(href)').get()
            if next_button:
                next_url = response.urljoin(next_button)
                yield scrapy.Request(
                    url=next_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_timeout", 3000),
                            PageMethod("wait_for_selector", "[data-testid='SearchResults']", timeout=10000),
                        ],
                    },
                    callback=self.parse_search_results,
                    errback=self.errback,
                )
    
    def parse_listing_details(self, response):
        """Parse individual listing page to extract all images and price"""
        item = response.meta['item']
        
        self.logger.info(f"Parsing detail page for: {item['title'][:60]}")
        self.logger.debug(f"Detail page URL: {response.url}")
        
        # Extract price from detail page (more reliable than search results)
        price = None
        
        # Method 1: Try data-testid selector
        price = response.css('[data-testid="ItemPrice"]::text').get()
        
        # Method 2: Try common price selectors
        if not price:
            price = response.css('.item-price::text').get()
        
        # Method 3: Look for price in meta tags
        if not price:
            price = response.css('meta[property="product:price:amount"]::attr(content)').get()
            if price:
                price = f"${price}"
        
        # Method 4: Use regex to find any dollar amount in the page
        if not price:
            price = response.css('*::text').re_first(r'\$[\d,]+\.?\d*')
        
        # Update item price if found
        if price:
            item['price'] = price
            self.logger.info(f"✅ Found price: {price}")
        else:
            self.logger.warning(f"⚠️  No price found on detail page")
        
        # Try multiple selectors to find all images on Mercari
        image_urls = []
        
        # Method 1: Main product image carousel/gallery (check both src and data-src)
        gallery_images = response.css('[data-testid="image-gallery"] img::attr(src)').getall()
        gallery_images.extend(response.css('[data-testid="image-gallery"] img::attr(data-src)').getall())
        if gallery_images:
            self.logger.info(f"Method 1: Found {len(gallery_images)} images in gallery")
            image_urls.extend(gallery_images)
        
        # Method 2: Item box images (Mercari's main image container)
        if not image_urls:
            item_box_images = response.css('[data-testid="item-box"] img::attr(src)').getall()
            item_box_images.extend(response.css('[data-testid="item-box"] img::attr(data-src)').getall())
            if item_box_images:
                self.logger.info(f"Method 2: Found {len(item_box_images)} item box images")
                image_urls.extend(item_box_images)
        
        # Method 3: Picture list or carousel
        if not image_urls:
            carousel_images = response.css('.carousel img::attr(src)').getall()
            carousel_images.extend(response.css('.carousel img::attr(data-src)').getall())
            if carousel_images:
                self.logger.info(f"Method 3: Found {len(carousel_images)} carousel images")
                image_urls.extend(carousel_images)
        
        # Method 4: Any image from Mercari/Cloudinary CDN (but filter out tracking pixels)
        if not image_urls:
            self.logger.warning(f"Methods 1-3 failed, trying method 4 for: {item['title'][:60]}")
            all_images = response.css('img::attr(src)').getall()
            all_images.extend(response.css('img::attr(data-src)').getall())
            self.logger.debug(f"Found {len(all_images)} total images on page")
            
            # Filter for Mercari/Cloudinary CDN URLs and exclude tracking pixels
            image_urls = [
                img for img in all_images 
                if img and (
                    ('cloudinary.com' in img and '/image/upload/' in img) or
                    ('mercdn.net' in img and '/photos/' in img) or  # Mercari's actual CDN
                    ('mercari-images' in img) or
                    ('mercari.com' in img and ('/photos/' in img or '/images/' in img))
                ) and not any(exclude in img for exclude in ['bat.bing.com', 'tracking', 'pixel', 'analytics', '/members/'])  # Exclude profile pics
            ]
            self.logger.info(f"Method 4: Filtered to {len(image_urls)} CDN images (excluded tracking pixels)")
        
        # Convert all thumbnails to high-resolution
        high_res_urls = []
        current_listing_id = item.get('listing_id', '')
        
        for img_url in image_urls:
            if img_url and img_url.strip():
                # Skip obvious tracking/analytics URLs
                if any(bad in img_url.lower() for bad in ['bat.bing.com', 'analytics', 'tracking', 'pixel', '/members/']):
                    self.logger.debug(f"Skipping tracking/profile URL: {img_url[:80]}")
                    continue
                
                # IMPORTANT: Only include images that belong to the current listing
                # Mercari shows "More from this seller" below the listing, we need to filter those out
                if current_listing_id and '/photos/' in img_url:
                    # Extract listing ID from image URL (e.g., m10481805901 from photos/m10481805901_1.jpg)
                    img_listing_match = re.search(r'/photos/(m\d+)_', img_url)
                    if img_listing_match:
                        img_listing_id = img_listing_match.group(1)
                        if img_listing_id != current_listing_id:
                            self.logger.debug(f"Skipping image from different listing: {img_listing_id} (current: {current_listing_id})")
                            continue
                
                # Mercari uses URL query parameters - optimize for high quality
                if 'mercdn.net' in img_url or 'mercari' in img_url:
                    # Replace width parameter with 2560 for maximum quality
                    high_res_url = re.sub(r'width=\d+', 'width=2560', img_url)
                    high_res_url = re.sub(r'quality=\d+', 'quality=95', high_res_url)
                    # Add width if not present
                    if 'width=' not in high_res_url:
                        separator = '&' if '?' in high_res_url else '?'
                        high_res_url += f'{separator}width=2560&quality=95'
                else:
                    # Cloudinary CDN - use path-based parameters
                    high_res_url = re.sub(r'/c_fill,[^/]+/', '/c_fit,f_auto,fl_progressive:steep,h_1600,q_95,w_1600/', img_url)
                    high_res_url = re.sub(r'/w_\d+,h_\d+/', '/w_1600,h_1600/', high_res_url)
                    high_res_url = re.sub(r'/q_\d+/', '/q_95/', high_res_url)
                
                # Avoid duplicates
                if high_res_url not in high_res_urls:
                    high_res_urls.append(high_res_url)
        
        # Update item with all images
        if high_res_urls:
            item['image_urls'] = high_res_urls
            self.logger.info(f"✅ Found {len(high_res_urls)} high-res images for listing {item.get('listing_id', 'unknown')}")
            for i, url in enumerate(high_res_urls, 1):
                self.logger.debug(f"   Image {i}: {url[:80]}...")
        else:
            self.logger.error(f"❌ NO IMAGES FOUND on detail page for: {item['title'][:60]}")
            self.logger.error(f"   Keeping {len(item.get('image_urls', []))} thumbnail(s) as fallback")
        
        yield item
    
    def errback(self, failure):
        """Handle errors"""
        logger.error(f"Request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")
    
    def extract_grading_info(self, title):
        """Extract grading company and grade from title"""
        grading_info = {
            'card_name': None,
            'grading_company': None,
            'grade': None,
        }
        
        # Common grading companies (including TAG)
        companies = ['PSA', 'BGS', 'CGC', 'SGC', 'TAG', 'Beckett']
        
        for company in companies:
            if company in title.upper():
                grading_info['grading_company'] = company
                
                # Try to extract grade (e.g., "PSA 10", "BGS 9.5", "TAG 10")
                pattern = rf'{company}\s*(\d+(?:\.\d+)?)'
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    grading_info['grade'] = match.group(1)
                break
        
        # Extract card name (basic heuristic - take first few words before grading info)
        if grading_info['grading_company']:
            parts = title.split(grading_info['grading_company'])
            if parts and parts[0].strip() != "":
                grading_info['card_name'] = parts[0].strip()
            else:
                grading_info['card_name'] = parts[-1].strip()
        else:
            # If no grading company found, use first part of title
            grading_info['card_name'] = title[:(len(title) // 2)]
        
        return grading_info
