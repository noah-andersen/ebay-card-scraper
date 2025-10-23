"""
Example usage of the multi-marketplace card scraper.
"""

from scrapers import EbayScraper, MercariScraper


def example_single_marketplace():
    """Example: Scrape a single marketplace"""
    print("\n" + "="*60)
    print("Example 1: Single Marketplace (eBay)")
    print("="*60 + "\n")
    
    # Initialize eBay scraper
    scraper = EbayScraper(output_dir='./data')
    
    # Search for PSA 10 cards
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=10,
        max_results=5  # Small number for testing
    )
    
    print(f"\n✓ Downloaded {count} images from eBay")


def example_multiple_marketplaces():
    """Example: Scrape multiple marketplaces"""
    print("\n" + "="*60)
    print("Example 2: Multiple Marketplaces")
    print("="*60 + "\n")
    
    total_count = 0
    
    # eBay
    print("Scraping eBay...")
    ebay = EbayScraper(output_dir='./data')
    count = ebay.search_graded_cards('BGS', 9.5, max_results=5)
    total_count += count
    print(f"✓ eBay: {count} images\n")
    
    # Mercari
    print("Scraping Mercari...")
    mercari = MercariScraper(output_dir='./data')
    count = mercari.search_graded_cards('BGS', 9.5, max_results=5)
    total_count += count
    print(f"✓ Mercari: {count} images\n")
    
    print(f"✓ Total: {total_count} images across all marketplaces")


def example_specific_card():
    """Example: Search for a specific card"""
    print("\n" + "="*60)
    print("Example 3: Specific Card Search")
    print("="*60 + "\n")
    
    # Search for Charizard PSA 10 on eBay
    scraper = EbayScraper(output_dir='./data')
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=10,
        card_name='Charizard',
        max_results=10
    )
    
    print(f"\n✓ Found {count} PSA 10 Charizard cards on eBay")


def example_sold_listings():
    """Example: Search eBay sold listings"""
    print("\n" + "="*60)
    print("Example 4: eBay Sold Listings")
    print("="*60 + "\n")
    
    scraper = EbayScraper(output_dir='./data')
    count = scraper.search_graded_cards(
        grading_company='CGC',
        grade=9,
        sold_only=True,
        max_results=10
    )
    
    print(f"\n✓ Found {count} sold CGC 9 cards on eBay")


def example_custom_output():
    """Example: Custom output directory"""
    print("\n" + "="*60)
    print("Example 5: Custom Output Directory")
    print("="*60 + "\n")
    
    # Create scraper with custom output directory
    scraper = MercariScraper(output_dir='./my_custom_data')
    count = scraper.search_graded_cards(
        grading_company='PSA',
        grade=9,
        max_results=5
    )
    
    print(f"\n✓ Saved {count} images to './my_custom_data/mercari/'")


def example_programmatic_iteration():
    """Example: Iterate through multiple grades programmatically"""
    print("\n" + "="*60)
    print("Example 6: Iterate Through Grades")
    print("="*60 + "\n")
    
    scraper = MercariScraper(output_dir='./data')
    
    # Search for PSA grades 8, 9, and 10
    grades = [8, 9, 10]
    total_count = 0
    
    for grade in grades:
        print(f"\nSearching for PSA {grade} cards...")
        count = scraper.search_graded_cards(
            grading_company='PSA',
            grade=grade,
            max_results=3  # Small number per grade
        )
        total_count += count
        print(f"✓ PSA {grade}: {count} images")
    
    print(f"\n✓ Total: {total_count} images across all grades")


def main():
    """Run examples"""
    print("\n" + "="*60)
    print("Graded Pokemon Card Scraper - Examples")
    print("="*60)
    
    print("\nAvailable examples:")
    print("1. Single marketplace (eBay)")
    print("2. Multiple marketplaces (eBay + Mercari)")
    print("3. Specific card search (Charizard)")
    print("4. eBay sold listings")
    print("5. Custom output directory")
    print("6. Iterate through grades")
    print("7. Run all examples")
    
    choice = input("\nSelect example (1-7): ").strip()
    
    examples = {
        '1': example_single_marketplace,
        '2': example_multiple_marketplaces,
        '3': example_specific_card,
        '4': example_sold_listings,
        '5': example_custom_output,
        '6': example_programmatic_iteration,
    }
    
    if choice == '7':
        # Run all examples
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n✗ Error: {e}\n")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
    else:
        print("\nInvalid choice. Exiting.")
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
