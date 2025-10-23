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
            # Extract basic info
            # Title is in the image alt attribute
            title = listing.css('img::attr(alt)').get()
            # Extract price using regex to find first dollar amount
            price = listing.css('*::text').re_first(r'\$[\d,]+\.?\d*')
            listing_url = listing.css('a.image-treatment::attr(href)').get()
            image_url = listing.css('img::attr(src)').get()
            
            # Debug logging
            self.logger.info(f"Item {i}: title={title}, price={price}, url={listing_url is not None}")
            
            if not title or not listing_url:
                self.logger.warning(f"Skipping item {i}: missing title or URL")
                continue
            
            # Extract grading information from title
            grading_info = self.extract_grading_info(title)
            
            # Create item
            item = GradedCardItem()
            item['title'] = title
            item['card_name'] = grading_info['card_name']
            item['grading_company'] = grading_info['grading_company']
            item['grade'] = grading_info['grade']
            item['price'] = price
            item['listing_url'] = listing_url
            item['image_urls'] = [image_url] if image_url else []
            item['source'] = 'ebay'
            item['scraped_date'] = datetime.now().isoformat()
            
            self.logger.info(f"Yielding item: {item['card_name']} - {item['grading_company']} {item['grade']}")
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
        
        # Common grading companies
        companies = ['PSA', 'BGS', 'CGC', 'SGC', 'Beckett']
        
        for company in companies:
            if company in title.upper():
                grading_info['grading_company'] = company
                
                # Try to extract grade (e.g., "PSA 10", "BGS 9.5")
                pattern = rf'{company}\s*(\d+(?:\.\d+)?)'
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    grading_info['grade'] = match.group(1)
                break
        
        # Extract card name (basic heuristic - take first few words before grading info)
        if grading_info['grading_company']:
            parts = title.split(grading_info['grading_company'])
            if parts:
                grading_info['card_name'] = parts[0].strip()
        else:
            # If no grading company found, use first part of title
            grading_info['card_name'] = title[:50]
        
        return grading_info
