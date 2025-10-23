import scrapy


class GradedCardItem(scrapy.Item):
    """Item for storing graded Pokemon card data"""
    
    # Card identification
    card_name = scrapy.Field()
    card_number = scrapy.Field()
    set_name = scrapy.Field()
    
    # Grading information
    grading_company = scrapy.Field()  # PSA, BGS, CGC, etc.
    grade = scrapy.Field()
    
    # Listing information
    title = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    condition = scrapy.Field()
    
    # Source information
    source = scrapy.Field()  # 'ebay' or 'mercari'
    listing_url = scrapy.Field()
    seller = scrapy.Field()
    
    # Images
    image_urls = scrapy.Field()
    images = scrapy.Field()
    
    # Metadata
    scraped_date = scrapy.Field()
