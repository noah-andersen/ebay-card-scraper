#!/usr/bin/env python3
"""
Example usage of the eBay Card Scraper
"""

from ebay_card_scraper import EbayCardScraper


def example_basic_search():
    """Example: Basic search for PSA graded Pokemon cards"""
    print("Example 1: Basic search for PSA graded cards")
    print("-" * 50)
    
    scraper = EbayCardScraper(output_dir="ebay_images")
    
    # Search for PSA graded Pokemon cards
    listings = scraper.search_graded_cards(
        grading_company="PSA",
        max_results=5
    )
    
    for listing in listings:
        print(f"Title: {listing.get('title')}")
        print(f"Price: {listing.get('price')}")
        print(f"URL: {listing.get('url')}")
        print()


def example_specific_card():
    """Example: Search for a specific card"""
    print("\nExample 2: Search for specific card (Charizard)")
    print("-" * 50)
    
    scraper = EbayCardScraper(output_dir="ebay_images")
    
    # Search for Charizard cards graded by BGS
    listings = scraper.search_graded_cards(
        grading_company="BGS",
        card_name="Charizard",
        max_results=3
    )
    
    for listing in listings:
        print(f"Title: {listing.get('title')}")
        print(f"Price: {listing.get('price')}")
        print()


def example_download_images():
    """Example: Search and download images"""
    print("\nExample 3: Search and download images")
    print("-" * 50)
    
    scraper = EbayCardScraper(output_dir="ebay_images")
    
    # Search and download images from PSA graded Pikachu cards
    results = scraper.scrape_and_download(
        grading_company="PSA",
        card_name="Pikachu",
        max_listings=2
    )
    
    print(f"Search Query: {results['search_query']}")
    print(f"Listings Found: {results['listings_found']}")
    print(f"Listings Downloaded: {results['listings_downloaded']}")
    print(f"Total Images: {results['total_images']}")
    
    # Show details for each listing
    for detail in results['details']:
        print(f"\n  Card: {detail['title']}")
        print(f"  Price: {detail['price']}")
        print(f"  Images Saved: {detail['images_saved']}")


def example_download_from_url():
    """Example: Download images from a specific URL"""
    print("\nExample 4: Download from specific listing URL")
    print("-" * 50)
    
    scraper = EbayCardScraper(output_dir="ebay_images")
    
    # Replace this with an actual eBay listing URL
    listing_url = "https://www.ebay.com/itm/123456789"
    
    saved_files = scraper.download_listing_images(
        listing_url=listing_url,
        card_name="My Pokemon Card"
    )
    
    print(f"Downloaded {len(saved_files)} images")
    for filepath in saved_files:
        print(f"  - {filepath}")


def example_all_grading_companies():
    """Example: Search across different grading companies"""
    print("\nExample 5: Compare across grading companies")
    print("-" * 50)
    
    scraper = EbayCardScraper(output_dir="ebay_images")
    
    companies = ["PSA", "BGS", "CGC", "SGC"]
    card_name = "Charizard"
    
    for company in companies:
        print(f"\n{company} Graded {card_name}:")
        listings = scraper.search_graded_cards(
            grading_company=company,
            card_name=card_name,
            max_results=3
        )
        print(f"  Found {len(listings)} listings")


if __name__ == "__main__":
    print("=" * 60)
    print("eBay Card Scraper - Usage Examples")
    print("=" * 60)
    print("\nNote: These examples require internet access to eBay.com")
    print("Uncomment the example you want to run:\n")
    
    # Uncomment the example you want to run:
    
    # example_basic_search()
    # example_specific_card()
    # example_download_images()
    # example_download_from_url()
    # example_all_grading_companies()
    
    print("\nTo run these examples, uncomment the desired function call above.")
    print("Or use the command-line interface:")
    print("  python ebay_card_scraper.py PSA --card 'Charizard' --max-listings 5")
