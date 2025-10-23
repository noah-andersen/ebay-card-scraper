#!/usr/bin/env python3
"""
Command-line interface for multi-marketplace card scraper.

Usage:
    python main.py --marketplace ebay --company PSA --grade 10 --max-results 50
    python main.py --marketplace mercari --company BGS --grade 9.5 --card-name Charizard --max-results 20
    python main.py --marketplace both --company CGC --grade 10 --max-results 100
"""

import argparse
import sys
from scrapers.ebay_scraper import EbayScraper
from scrapers.mercari_scraper import MercariScraper
import config


def main():
    parser = argparse.ArgumentParser(
        description='Scrape marketplaces for graded Pokemon card images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Search eBay for PSA 10 cards:
    python main.py --marketplace ebay --company PSA --grade 10 --max-results 50

  Search Mercari for BGS 9.5 Charizard cards:
    python main.py --marketplace mercari --company BGS --grade 9.5 --card-name Charizard --max-results 20

  Search both marketplaces for CGC 10:
    python main.py --marketplace both --company CGC --grade 10 --max-results 50

  Search eBay sold listings only:
    python main.py --marketplace ebay --company PSA --grade 10 --sold-only --max-results 30
        """
    )
    
    parser.add_argument(
        '--marketplace',
        type=str,
        required=True,
        choices=['ebay', 'mercari', 'both'],
        help='Marketplace to scrape (ebay, mercari, or both)'
    )
    
    parser.add_argument(
        '--company',
        type=str,
        required=True,
        choices=['PSA', 'BGS', 'BECKETT', 'CGC'],
        help='Grading company (PSA, BGS, or CGC)'
    )
    
    parser.add_argument(
        '--grade',
        type=float,
        required=True,
        help='Card grade (1-10, or 9.5 for BGS)'
    )
    
    parser.add_argument(
        '--card-name',
        type=str,
        help='Specific card name to search for (e.g., "Charizard")'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of results to scrape per marketplace (default: 50)'
    )
    
    parser.add_argument(
        '--sold-only',
        action='store_true',
        help='Search only sold/completed listings (eBay only)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'Output directory for images and metadata (default: {config.OUTPUT_DIR})'
    )
    
    args = parser.parse_args()
    
    # Determine which marketplaces to scrape
    marketplaces = []
    if args.marketplace == 'both':
        marketplaces = ['ebay', 'mercari']
    else:
        marketplaces = [args.marketplace]
    
    # Initialize
    print("\n" + "="*60)
    print("Graded Pokemon Card Scraper")
    print("="*60 + "\n")
    
    total_count = 0
    
    try:
        for marketplace in marketplaces:
            print(f"\nScraping {marketplace.upper()}...")
            print("-"*60)
            
            # Initialize scraper
            if marketplace == 'ebay':
                scraper = EbayScraper(output_dir=args.output_dir)
            elif marketplace == 'mercari':
                scraper = MercariScraper(output_dir=args.output_dir)
            else:
                continue
            
            # Search
            count = scraper.search_graded_cards(
                grading_company=args.company,
                grade=args.grade,
                card_name=args.card_name,
                max_results=args.max_results,
                sold_only=args.sold_only if marketplace == 'ebay' else False
            )
            
            total_count += count
            print(f"✓ Downloaded {count} images from {marketplace.upper()}")
        
        print(f"\n{'='*60}")
        print(f"✓ Complete! Total downloaded: {total_count} images")
        print(f"{'='*60}\n")
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
