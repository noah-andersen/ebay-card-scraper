import scrapy
from scrapy_playwright.page import PageMethod
from graded_cards_scraper.items import GradedCardItem
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EbayGradedCardsSpider(scrapy.Spider):
    name = "ebay_graded_cards"
    allowed_domains = ["ebay.com", "ebayimg.com"]  # Allow both eBay and its image server
    
    def __init__(self, search_query="PSA 10 Pokemon Card", max_pages=5, *args, **kwargs):
        super(EbayGradedCardsSpider, self).__init__(*args, **kwargs)
        self.search_query = search_query
        self.max_pages = int(max_pages)
        self.page_count = 0
        self.items_processed = 0  # Track number of items processed
    
    def start_requests(self):
        """Start scraping from eBay search results"""
        base_url = "https://www.ebay.com/sch/i.html"
        search_url = f"{base_url}?_nkw={self.search_query.replace(' ', '+')}&_ipg=240"
        
        yield scrapy.Request(
            url=search_url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 3000),
                    PageMethod("evaluate", "() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); }"),
                ],
            },
            callback=self.parse_search_results,
            errback=self.errback,
        )
    
    def parse_search_results(self, response):
        """Parse eBay search results page"""
        # Get all listing items - use the correct selector
        listings = response.css('ul.srp-results li')
        
        self.logger.info(f"Found {len(listings)} listings on page")
        
        for i, listing in enumerate(listings):
            # Check if we've hit the item limit (if CLOSESPIDER_ITEMCOUNT is set)
            closespider_itemcount = self.crawler.settings.getint('CLOSESPIDER_ITEMCOUNT', 0)
            if closespider_itemcount > 0 and self.items_processed >= closespider_itemcount:
                self.logger.info(f"Reached item limit ({closespider_itemcount}), stopping processing")
                break
            
            # Extract basic info
            # Title is in the image alt attribute
            title = listing.css('img::attr(alt)').get()
            # Extract price using regex to find first dollar amount
            price = listing.css('*::text').re_first(r'\$[\d,]+\.?\d*')
            listing_url = listing.css('a.image-treatment::attr(href)').get()
            image_url = listing.css('img::attr(src)').get()
            
            # Convert thumbnail to high-resolution image URL
            # eBay image URLs use parameters like s-l140.jpg (140px) or s-l225.jpg (225px)
            # Replace with s-l1600.jpg (1600px) or s-l1200.jpg (1200px) for higher resolution
            if image_url:
                # Replace size parameter with maximum resolution
                import re
                # Pattern matches s-l[number].jpg or s-l[number].png
                high_res_url = re.sub(r's-l\d+', 's-l1600', image_url)
                # Also try replacing other common thumbnail patterns
                high_res_url = high_res_url.replace('$_1.JPG', '$_57.JPG')  # eBay's full size format
                high_res_url = high_res_url.replace('$_12.JPG', '$_57.JPG')
                high_res_url = high_res_url.replace('$_14.JPG', '$_57.JPG')
                image_url = high_res_url
                self.logger.debug(f"High-res image URL: {image_url}")
            
            # Debug logging
            self.logger.info(f"Item {i}: title={title}, price={price}, url={listing_url is not None}")
            
            if not title or not listing_url:
                self.logger.warning(f"Skipping item {i}: missing title or URL")
                continue
            
            # Increment counter when we process a listing
            self.items_processed += 1
            
            # Extract grading information from title
            grading_info = self.extract_grading_info(title)
            
            # Extract listing ID from URL for folder organization
            import re
            listing_id = None
            if listing_url:
                # eBay item IDs are typically in the URL like /itm/123456789 or ?item=123456789
                id_match = re.search(r'/itm/(\d+)|[\?&]item=(\d+)', listing_url)
                if id_match:
                    listing_id = id_match.group(1) or id_match.group(2)
            
            # Create temporary item with basic info to pass to detail page
            item = GradedCardItem()
            item['title'] = title
            item['card_name'] = grading_info['card_name']
            item['grading_company'] = grading_info['grading_company']
            item['grade'] = grading_info['grade']
            item['price'] = price
            item['listing_url'] = listing_url
            item['listing_id'] = listing_id
            item['image_urls'] = [image_url] if image_url else []  # Thumbnail as fallback
            item['source'] = 'ebay'
            item['scraped_date'] = datetime.now().isoformat()
            
            # Follow listing URL to get all images
            if listing_url:
                self.logger.info(f"Following listing for all images: {item['card_name']}")
                yield response.follow(
                    listing_url,
                    callback=self.parse_listing_details,
                    meta={'item': item, 'playwright': True},
                    dont_filter=True
                )
            else:
                # No URL available, yield item with thumbnail only
                self.logger.info(f"Yielding item (no detail page): {item['card_name']}")
                yield item
    
    def parse_listing_details(self, response):
        """Parse individual listing page to extract all images"""
        item = response.meta['item']
        
        self.logger.info(f"Parsing detail page for: {item['title'][:60]}")
        self.logger.debug(f"Detail page URL: {response.url}")
        
        # Try multiple selectors to find all images
        image_urls = []
        
        # Method 1: eBay's image carousel/gallery (most common)
        gallery_images = response.css('img.vi-image-gallery__image::attr(src)').getall()
        if gallery_images:
            self.logger.info(f"Method 1: Found {len(gallery_images)} images in gallery")
            image_urls.extend(gallery_images)
        
        # Method 2: Main product image and thumbnails
        if not image_urls:
            main_image = response.css('#icImg::attr(src)').get()
            if main_image:
                self.logger.info(f"Method 2: Found main image")
                image_urls.append(main_image)
            
            thumb_images = response.css('#vi_main_img_fs img::attr(src)').getall()
            if thumb_images:
                self.logger.info(f"Method 2: Found {len(thumb_images)} thumb images")
                image_urls.extend(thumb_images)
        
        # Method 3: Picture panel images
        if not image_urls:
            panel_images = response.css('.ux-image-carousel-item img::attr(src)').getall()
            if panel_images:
                self.logger.info(f"Method 3: Found {len(panel_images)} images in carousel")
                image_urls.extend(panel_images)
        
        # Method 4: Any high-resolution image in the listing
        if not image_urls:
            self.logger.warning(f"Methods 1-3 failed, trying method 4 for: {item['title'][:60]}")
            all_images = response.css('img::attr(src)').getall()
            self.logger.debug(f"Found {len(all_images)} total images on page")
            # Filter for eBay image CDN URLs
            image_urls = [img for img in all_images if 'ebayimg.com' in img and 's-l' in img]
            self.logger.info(f"Method 4: Filtered to {len(image_urls)} eBay CDN images")
        
        # Convert all thumbnails to high-resolution
        import re
        high_res_urls = []
        for img_url in image_urls:
            if img_url:
                # Replace size parameter with maximum resolution
                high_res_url = re.sub(r's-l\d+', 's-l1600', img_url)
                high_res_url = high_res_url.replace('$_1.JPG', '$_57.JPG')
                high_res_url = high_res_url.replace('$_12.JPG', '$_57.JPG')
                high_res_url = high_res_url.replace('$_14.JPG', '$_57.JPG')
                high_res_url = high_res_url.replace('$_35.JPG', '$_57.JPG')
                
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
        
        # Skip listings with more than 5 images
        if len(item.get('image_urls', [])) > 5:
            self.logger.warning(f"⏭️  SKIPPING listing with {len(item['image_urls'])} images (max 5): {item['title'][:60]}")
            return
        
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
                
                # For TAG and CGC, check for "10 Pristine" grade first
                if company in ['TAG', 'CGC']:
                    pristine_pattern = rf'{company}\s*10\s*Pristine'
                    pristine_match = re.search(pristine_pattern, title, re.IGNORECASE)
                    if pristine_match:
                        grading_info['grade'] = '10 Pristine'
                        break
                
                # Try to extract standard grade (e.g., "PSA 10", "BGS 9.5", "TAG 10", "CGC 9")
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
