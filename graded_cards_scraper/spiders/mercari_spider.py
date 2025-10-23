import scrapy
from scrapy_playwright.page import PageMethod
from graded_cards_scraper.items import GradedCardItem
import re
import logging
import json

logger = logging.getLogger(__name__)


class MercariGradedCardsSpider(scrapy.Spider):
    name = "mercari_graded_cards"
    allowed_domains = ["mercari.com"]
    
    def __init__(self, search_query="PSA 10 Pokemon Card", max_pages=5, *args, **kwargs):
        super(MercariGradedCardsSpider, self).__init__(*args, **kwargs)
        self.search_query = search_query
        self.max_pages = int(max_pages)
        self.page_count = 0
    
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
        
        logger.info(f"Found {len(listings)} listings on page {self.page_count + 1}")
        
        for listing in listings:
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
                import re
                # Remove size restrictions and set to high quality
                high_res_url = re.sub(r'/c_fill,[^/]+/', '/c_fit,f_auto,fl_progressive:steep,h_1600,q_95,w_1600/', image_url)
                # Also handle other common patterns
                high_res_url = re.sub(r'/w_\d+,h_\d+/', '/w_1600,h_1600/', high_res_url)
                high_res_url = re.sub(r'/q_\d+/', '/q_95/', high_res_url)
                image_url = high_res_url
                self.logger.debug(f"High-res image URL: {image_url}")
            
            image_urls = [image_url] if image_url else []
            
            if title:
                # Parse grading information from title
                grading_info = self.extract_grading_info(title)
                
                item = GradedCardItem(
                    title=title.strip(),
                    price=price.strip() if price else None,
                    currency='USD',
                    listing_url=listing_url,
                    source='mercari',
                    image_urls=image_urls,
                    card_name=grading_info.get('card_name'),
                    grading_company=grading_info.get('grading_company'),
                    grade=grading_info.get('grade'),
                )
                
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
                )
    
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
            if parts:
                grading_info['card_name'] = parts[0].strip()
        else:
            # If no grading company found, use first part of title
            grading_info['card_name'] = title[:50]
        
        return grading_info
