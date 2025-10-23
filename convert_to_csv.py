#!/usr/bin/env python3
"""
Command-line interface for converting scraper JSON output to CSV format.

Usage:
    python convert_to_csv.py output.json
    python convert_to_csv.py output.json --csv cards.csv
    python convert_to_csv.py output.json --with-stats
    python convert_to_csv.py --batch scraped_data/
    python convert_to_csv.py --merge output1.csv output2.csv --output all_cards.csv
"""

import argparse
import sys
from pathlib import Path
from graded_cards_scraper.utils import (
    json_to_csv, 
    json_to_csv_with_stats, 
    batch_json_to_csv,
    merge_csv_files
)


def main():
    parser = argparse.ArgumentParser(
        description='Convert graded cards scraper JSON output to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single JSON file to CSV
  python convert_to_csv.py output.json
  
  # Convert with custom output name
  python convert_to_csv.py output.json --csv cards.csv
  
  # Convert and generate statistics
  python convert_to_csv.py output.json --with-stats
  
  # Batch convert all JSON files in a directory
  python convert_to_csv.py --batch scraped_data/
  
  # Merge multiple CSV files
  python convert_to_csv.py --merge output1.csv output2.csv -o all_cards.csv
        """
    )
    
    # Main arguments
    parser.add_argument('input', nargs='?', help='Input JSON file path')
    parser.add_argument('--csv', '-c', dest='csv_output', help='Output CSV file path')
    parser.add_argument('--with-stats', '-s', action='store_true', 
                       help='Generate statistics file along with CSV')
    parser.add_argument('--stats', dest='stats_output', help='Custom statistics file path')
    
    # Batch mode
    parser.add_argument('--batch', '-b', dest='batch_dir', 
                       help='Convert all JSON files in a directory')
    parser.add_argument('--output-dir', '-d', dest='output_dir',
                       help='Output directory for batch conversion')
    
    # Merge mode
    parser.add_argument('--merge', '-m', nargs='+', dest='merge_files',
                       help='Merge multiple CSV files')
    parser.add_argument('--output', '-o', dest='merge_output',
                       help='Output path for merged CSV')
    parser.add_argument('--keep-duplicates', action='store_true',
                       help='Keep duplicate entries when merging')
    
    args = parser.parse_args()
    
    try:
        # Batch conversion mode
        if args.batch_dir:
            print(f"Converting all JSON files in {args.batch_dir}...")
            csv_files = batch_json_to_csv(args.batch_dir, args.output_dir)
            print(f"\n✓ Successfully converted {len(csv_files)} files:")
            for csv_file in csv_files:
                print(f"  - {csv_file}")
            return 0
        
        # Merge mode
        if args.merge_files:
            if not args.merge_output:
                print("Error: --output (-o) is required when using --merge")
                return 1
            
            print(f"Merging {len(args.merge_files)} CSV files...")
            merged_path = merge_csv_files(
                args.merge_files, 
                args.merge_output,
                remove_duplicates=not args.keep_duplicates
            )
            print(f"✓ Successfully merged files to: {merged_path}")
            return 0
        
        # Single file conversion mode
        if not args.input:
            parser.print_help()
            return 1
        
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}")
            return 1
        
        if args.with_stats or args.stats_output:
            print(f"Converting {args.input} to CSV with statistics...")
            result = json_to_csv_with_stats(
                args.input,
                csv_path=args.csv_output,
                stats_path=args.stats_output
            )
            print(f"\n✓ CSV saved to: {result['csv']}")
            print(f"✓ Statistics saved to: {result['stats']}")
        else:
            print(f"Converting {args.input} to CSV...")
            csv_path = json_to_csv(args.input, args.csv_output)
            print(f"✓ CSV saved to: {csv_path}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
