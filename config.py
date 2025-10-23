# Configuration settings for eBay scraper

# eBay search settings
EBAY_BASE_URL = "https://www.ebay.com/sch/i.html"
EBAY_SOLD_BASE_URL = "https://www.ebay.com/sch/i.html?LH_Sold=1&LH_Complete=1"

# Grading companies
GRADING_COMPANIES = {
    'PSA': 'PSA',
    'BGS': 'BGS',
    'BECKETT': 'BGS',
    'CGC': 'CGC',
    'TAG': 'TAG'
}

# Valid grades
PSA_GRADES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
BGS_GRADES = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10]
CGC_GRADES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Scraping settings
REQUEST_DELAY_MIN = 3  # Minimum seconds between requests (increased for reliability)
REQUEST_DELAY_MAX = 7  # Maximum seconds between requests (increased for reliability)
MAX_RETRIES = 3
TIMEOUT = 60  # Request timeout in seconds (increased from 30)

# Output settings
OUTPUT_DIR = './data'
IMAGES_DIR = './data/images'
METADATA_FILE = './data/metadata.csv'

# Image settings
IMAGE_FORMAT = 'jpg'
IMAGE_QUALITY = 95
MAX_IMAGE_SIZE = (2048, 2048)  # Max width, height

# User agent for requests
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = './scraper.log'
