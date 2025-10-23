from scrapy import signals
from scrapy.http import HtmlResponse
import logging

logger = logging.getLogger(__name__)


class GradedCardsScraperDownloaderMiddleware:
    """Downloader middleware for handling requests"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        logger.error(f"Exception processing {request.url}: {exception}")

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")
