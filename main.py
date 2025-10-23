#!/usr/bin/env python3
"""
Command-line interface for eBay card scraper.

Usage:
    python main.py --company PSA --grade 10 --max-results 50
    python main.py --company BGS --grade 9.5 --card-name Charizard --max-results 20
    python main.py --company CGC --all-grades --max-results 100
"""

import argparse
import sys
from scraper import EbayScraper
import config


def main():
    parser = argparse.ArgumentParser(
        description='Scrape eBay for graded Pokemon card images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Search for PSA 10 cards:
    python main.py --company PSA --grade 10 --max-results 50

  Search for BGS 9.5 Charizard cards:
    python main.py --company BGS --grade 9.5 --card-name Charizard --max-results 20

  Search all grades for CGC:
    python main.py --company CGC --all-grades --max-results-per-grade 20

  Search sold listings only:
    python main.py --company PSA --grade 10 --sold-only --max-results 30
        """
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
        help='Maximum number of results to scrape (default: 50)'
    )
    
    parser.add_argument(
        '--max-results-per-grade',
        type=int,
        default=20,
        help='Maximum results per grade when using --all-grades (default: 20)'
    )
    
    parser.add_argument(
        '--all-grades',
        action='store_true',
        help='Search all grades for the specified company'
    )
    
    parser.add_argument(
        '--sold-only',
        action='store_true',
        help='Search only sold/completed listings'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'Output directory for images and metadata (default: {config.OUTPUT_DIR})'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all_grades and args.grade is None:
        parser.error("Either --grade or --all-grades must be specified")
    
    if args.all_grades and args.grade is not None:
        parser.error("Cannot specify both --grade and --all-grades")
    
    # Initialize scraper
    print("\n" + "="*60)
    print("eBay Graded Pokemon Card Scraper")
    print("="*60 + "\n")
    
    scraper = EbayScraper(output_dir=args.output_dir)
    
    try:
        if args.all_grades:
            # Search all grades
            scraper.search_all_grades(
                grading_company=args.company,
                card_name=args.card_name,
                max_results_per_grade=args.max_results_per_grade,
                sold_only=args.sold_only
            )
        else:
            # Search specific grade
            count = scraper.search_graded_cards(
                grading_company=args.company,
                grade=args.grade,
                card_name=args.card_name,
                max_results=args.max_results,
                sold_only=args.sold_only
            )
            
            print(f"\n{'='*60}")
            print(f"Successfully downloaded {count} images")
            print(f"{'='*60}\n")
    
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
