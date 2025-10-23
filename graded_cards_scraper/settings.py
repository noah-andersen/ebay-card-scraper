BOT_NAME = "graded_cards_scraper"

SPIDER_MODULES = ["graded_cards_scraper.spiders"]
NEWSPIDER_MODULE = "graded_cards_scraper.spiders"

# Crawl responsibly by identifying yourself
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Allow downloading images from eBay's image server
ALLOWED_DOMAINS = []  # Empty list allows all domains

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "graded_cards_scraper.middlewares.GradedCardsScraperDownloaderMiddleware": 543,
}

# Enable Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--disable-blink-features=AutomationControlled",
    ],
}

PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "java_script_enabled": True,
    }
}

# Enable image pipeline
ITEM_PIPELINES = {
    "graded_cards_scraper.pipelines.ImageDownloadPipeline": 1,
    "graded_cards_scraper.pipelines.GradedCardsScraperPipeline": 300,
}

# Enable extensions
EXTENSIONS = {
    'graded_cards_scraper.extensions.JsonToCsvExtension': 500,
}

# JSON to CSV conversion settings
JSON_TO_CSV_ENABLED = True  # Set to False to disable auto-conversion
JSON_TO_CSV_WITH_STATS = True  # Generate statistics file along with CSV

# Images will be stored in this directory
IMAGES_STORE = "downloaded_images"

# Image Pipeline Settings for High-Resolution Training Data
# Disable image thumbnailing to keep original resolution
IMAGES_THUMBS = {}  # Empty dict disables thumbnail generation

# Set minimum image dimensions (smaller images will be filtered out)
# This ensures you only get quality images for AI training
IMAGES_MIN_HEIGHT = 400
IMAGES_MIN_WIDTH = 400

# Disable image expiration (keep all images)
IMAGES_EXPIRES = 0  # Never expire images

# Image download settings
MEDIA_ALLOW_REDIRECTS = True  # Follow redirects to get actual image
IMAGES_RESULT_FIELD = 'images'  # Field name to store downloaded image paths

# Download timeout for large images
DOWNLOAD_TIMEOUT = 30  # Increased timeout for high-res images

# Configure item pipelines
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
