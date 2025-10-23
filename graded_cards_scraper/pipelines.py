from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
import scrapy
import logging
import os
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageDownloadPipeline(ImagesPipeline):
    """Pipeline for downloading and storing card images"""
    
    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        for image_url in adapter.get("image_urls", []):
            yield scrapy.Request(image_url, meta={'item': item})
    
    def file_path(self, request, response=None, info=None, *, item=None):
        """Generate custom file path for images"""
        image_url = request.url
        adapter = ItemAdapter(item)
        
        source = adapter.get("source", "unknown")
        card_name = adapter.get("card_name", "unknown").replace(" ", "_")
        grade = adapter.get("grade", "ungraded")
        grading_company = adapter.get("grading_company", "unknown")
        
        # Extract file extension
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1]
        if not ext:
            ext = ".jpg"
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}/{grading_company}/{card_name}_{grade}_{timestamp}{ext}"
        
        return filename
    
    def item_completed(self, results, item, info):
        adapter = ItemAdapter(item)
        image_paths = [x['path'] for ok, x in results if ok]
        
        if not image_paths:
            logger.warning(f"No images downloaded for item: {adapter.get('title')}")
        
        adapter['images'] = image_paths
        return item


class GradedCardsScraperPipeline:
    """Main pipeline for processing scraped items"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Add scraped date
        adapter['scraped_date'] = datetime.now().isoformat()
        
        # Validate required fields
        required_fields = ['title', 'listing_url', 'source']
        for field in required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")
        
        # Clean price field
        if adapter.get('price'):
            price_str = adapter['price']
            # Remove currency symbols and commas
            cleaned_price = ''.join(c for c in price_str if c.isdigit() or c == '.')
            try:
                adapter['price'] = float(cleaned_price) if cleaned_price else None
            except ValueError:
                adapter['price'] = None
        
        logger.info(f"Processed item: {adapter['title']}")
        return item
