"""
Example usage of the eBay card scraper.
Run this file to see how to use the scraper programmatically.
"""

from scraper import EbayScraper
import config


def example_basic_search():
    """Example: Basic search for PSA 10 Pokemon cards"""
    print("\n" + "="*60)
    print("Example 1: Basic Search - PSA 10 Pokemon Cards")
    print("="*60 + "\n")
    
    scraper = EbayScraper()
    
    # Search for PSA 10 graded Pokemon cards
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=10,
        max_results=10  # Start with small number for testing
    )
    
    print(f"\nDownloaded {count} images")


def example_specific_card():
    """Example: Search for specific card - Charizard"""
    print("\n" + "="*60)
    print("Example 2: Specific Card Search - BGS 9.5 Charizard")
    print("="*60 + "\n")
    
    scraper = EbayScraper()
    
    # Search for BGS 9.5 Charizard cards
    count = scraper.search_graded_cards(
        grading_company='BGS',
        grade=9.5,
        card_name='Charizard',
        max_results=5
    )
    
    print(f"\nDownloaded {count} Charizard images")


def example_sold_listings():
    """Example: Search sold listings for price data"""
    print("\n" + "="*60)
    print("Example 3: Sold Listings - CGC 10 Pokemon Cards")
    print("="*60 + "\n")
    
    scraper = EbayScraper()
    
    # Search sold listings to get actual sale prices
    count = scraper.search_graded_cards(
        grading_company='CGC',
        grade=10,
        max_results=5,
        sold_only=True
    )
    
    print(f"\nDownloaded {count} sold listing images")


def example_all_grades():
    """Example: Search all grades for PSA cards"""
    print("\n" + "="*60)
    print("Example 4: All Grades - PSA Pokemon Cards")
    print("="*60 + "\n")
    
    scraper = EbayScraper()
    
    # This will search PSA 1, 1.5, 2, 2.5, ..., 9.5, 10
    # With 5 results per grade
    scraper.search_all_grades(
        grading_company='PSA',
        max_results_per_grade=5
    )
    
    print("\nCompleted searching all PSA grades")


def example_view_statistics():
    """Example: View statistics of scraped data"""
    print("\n" + "="*60)
    print("Example 5: View Statistics")
    print("="*60 + "\n")
    
    from utils import print_statistics
    
    print_statistics(config.METADATA_FILE)


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║       eBay Graded Pokemon Card Scraper - Examples        ║
    ╚══════════════════════════════════════════════════════════╝
    
    This script demonstrates various ways to use the scraper.
    
    Choose an example to run:
    1. Basic search - PSA 10 cards
    2. Specific card search - BGS 9.5 Charizard
    3. Sold listings - CGC 10 cards
    4. All grades - PSA all grades
    5. View statistics
    
    Or modify this file to create your own custom searches!
    """)
    
    choice = input("Enter example number (1-5) or 'q' to quit: ").strip()
    
    examples = {
        '1': example_basic_search,
        '2': example_specific_card,
        '3': example_sold_listings,
        '4': example_all_grades,
        '5': example_view_statistics
    }
    
    if choice in examples:
        try:
            examples[choice]()
        except KeyboardInterrupt:
            print("\n\nExample interrupted by user")
        except Exception as e:
            print(f"\nError: {e}")
    elif choice.lower() == 'q':
        print("Goodbye!")
    else:
        print("Invalid choice")
