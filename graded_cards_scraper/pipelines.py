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
    """Pipeline for downloading and storing card images with high-resolution support"""
    
    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        for image_url in adapter.get("image_urls", []):
            logger.info(f"Requesting high-res image: {image_url}")
            yield scrapy.Request(image_url, meta={'item': item})
    
    def file_path(self, request, response=None, info=None, *, item=None):
        """Generate custom file path for images - organized by listing ID"""
        image_url = request.url
        adapter = ItemAdapter(item)
        
        source = adapter.get("source", "unknown")
        card_name = adapter.get("card_name")
        
        # Handle empty, None, or whitespace-only card_name
        if not card_name:
            # Use first 50 chars of title as fallback
            title = adapter.get("title", "unknown")
            card_name = title[:50] if title else "card"
            logger.debug(f"Using title as card_name fallback: {card_name[:30]}...")
        
        # Clean card_name for use in filesystem
        card_name = card_name.replace(" ", "_")[:50]  # Limit length
        # Remove special characters that cause issues
        card_name = "".join(c for c in card_name if c.isalnum() or c in "_-")
        
        grade = adapter.get("grade", "ungraded")
        grading_company = adapter.get("grading_company", "unknown")
        listing_id = adapter.get("listing_id", "unknown")
        
        # Extract file extension
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1]
        if not ext:
            ext = ".jpg"
        
        # Extract a simple image index from the URL or generate one
        # This helps differentiate multiple images from the same listing
        import hashlib
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        
        # Create folder structure: source/grading_company/listing_id_cardname_grade/image_hash.ext
        # This groups all images from the same listing together
        folder_name = f"{listing_id}_{card_name}_{grade}".replace("/", "-").replace("\\", "-")
        filename = f"{source}/{grading_company}/{folder_name}/image_{url_hash}{ext}"
        
        return filename
    
    def item_completed(self, results, item, info):
        adapter = ItemAdapter(item)
        image_paths = []
        
        # Check if we have any results
        if not results:
            logger.warning(f"No image download results for item: {adapter.get('title')}")
            adapter['images'] = []
            return item
        
        for ok, result in results:
            if ok:
                image_paths.append(result['path'])
                # Log image dimensions for quality verification
                if 'width' in result and 'height' in result:
                    logger.info(f"Downloaded high-res image: {result['path']} "
                              f"(Size: {result['width']}x{result['height']}px, "
                              f"Quality: {'Good' if result['width'] >= 800 else 'Low'})")
            else:
                logger.error(f"Failed to download image for {adapter.get('title')}: {result}")
        
        if not image_paths:
            logger.warning(f"No images downloaded for item: {adapter.get('title')} (had {len(adapter.get('image_urls', []))} URLs)")
        else:
            logger.info(f"Successfully downloaded {len(image_paths)} high-resolution image(s) "
                       f"for: {adapter.get('title')}")
        
        # Make sure to set images field even if empty
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
