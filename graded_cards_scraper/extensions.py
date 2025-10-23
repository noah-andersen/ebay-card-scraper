"""
Scrapy extension to automatically convert JSON output to CSV after scraping.
"""
from scrapy import signals
from scrapy.exceptions import NotConfigured
import logging
from pathlib import Path
from graded_cards_scraper.utils import json_to_csv, json_to_csv_with_stats

logger = logging.getLogger(__name__)


class JsonToCsvExtension:
    """
    Extension that converts JSON output to CSV after spider closes.
    
    Enable in settings.py:
        EXTENSIONS = {
            'graded_cards_scraper.extensions.JsonToCsvExtension': 500,
        }
        
        # Optional settings
        JSON_TO_CSV_ENABLED = True  # Enable/disable the extension
        JSON_TO_CSV_WITH_STATS = True  # Generate statistics file
    """
    
    def __init__(self, enabled, with_stats):
        self.enabled = enabled
        self.with_stats = with_stats
        self.json_files = set()
    
    @classmethod
    def from_crawler(cls, crawler):
        # Get settings
        enabled = crawler.settings.getbool('JSON_TO_CSV_ENABLED', True)
        with_stats = crawler.settings.getbool('JSON_TO_CSV_WITH_STATS', True)
        
        if not enabled:
            raise NotConfigured('JsonToCsvExtension is disabled')
        
        ext = cls(enabled, with_stats)
        
        # Connect to signals
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        
        return ext
    
    def item_scraped(self, item, response, spider):
        """Track JSON feed exports."""
        # Get feed exports from spider settings
        if hasattr(spider, 'settings'):
            feeds = spider.settings.get('FEEDS', {})
            for feed_uri in feeds:
                if feed_uri.endswith('.json'):
                    self.json_files.add(feed_uri)
    
    def spider_closed(self, spider, reason):
        """Convert JSON files to CSV when spider closes."""
        # Get output file from command line (-O flag)
        if hasattr(spider, 'crawler') and hasattr(spider.crawler, 'settings'):
            settings = spider.crawler.settings
            
            # Check for FEEDS setting (used by -O and -o flags)
            feeds = settings.getdict('FEEDS', {})
            for feed_uri in feeds:
                if feed_uri.endswith('.json'):
                    self.json_files.add(feed_uri)
        
        if not self.json_files:
            logger.info("No JSON files to convert (use -O output.json to enable auto-conversion)")
            return
        
        logger.info(f"Converting {len(self.json_files)} JSON file(s) to CSV...")
        
        for json_file in self.json_files:
            json_path = Path(json_file)
            
            if not json_path.exists():
                logger.warning(f"JSON file not found: {json_file}")
                continue
            
            try:
                if self.with_stats:
                    result = json_to_csv_with_stats(json_path)
                    logger.info(f"✓ Created CSV: {result['csv']}")
                    logger.info(f"✓ Created stats: {result['stats']}")
                else:
                    csv_path = json_to_csv(json_path)
                    logger.info(f"✓ Created CSV: {csv_path}")
                    
            except Exception as e:
                logger.error(f"Failed to convert {json_file} to CSV: {e}")
