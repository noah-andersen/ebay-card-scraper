"""
CSV Filter Script for Pokemon Card Data

This script filters out entries from CSV files based on:
1. Entries with 1 or 0 images listed under the images column
2. Entries containing the word "thicc" (case-insensitive)
3. Entries with missing grades that cannot be extracted via NLP from card_name

When a record is removed, associated image files are also deleted.
"""

import csv
import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. Install with: pip install spacy")
    print("Also download model with: python -m spacy download en_core_web_sm")


def count_images(images_str: str) -> int:
    """
    Count the number of images in the images column.
    Images are comma-separated.
    """
    if not images_str or images_str.strip() == "":
        return 0
    # Split by comma and count non-empty entries
    images = [img.strip() for img in images_str.split(',') if img.strip()]
    return len(images)


def contains_thicc(text: str) -> bool:
    """
    Check if text contains the word 'thicc' (case-insensitive).
    """
    if not text:
        return False
    return bool(re.search(r'\bthicc\b', text, re.IGNORECASE))


def contains_multiple_cards(text: str) -> bool:
    """
    Check if text indicates multiple cards in a listing.
    This helps avoid false positives where numbers refer to quantity, not grade.
    
    Args:
        text: The card name or title text
    
    Returns:
        True if text suggests multiple cards, False otherwise
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Pattern 1: Explicit quantity indicators with "cards"
    # e.g., "10 cards", "5 Pokemon cards", "20+ cards"
    quantity_patterns = [
        r'\b\d+\s*(?:pokemon\s+)?cards?\b',  # "10 cards", "5 pokemon cards"
        r'\b\d+\s*(?:graded\s+)?cards?\b',   # "10 graded cards"
        r'\b\d+\+\s*cards?\b',               # "20+ cards"
    ]
    
    for pattern in quantity_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Pattern 2: Words indicating collections/lots/sets
    collection_keywords = [
        r'\blot\b',
        r'\bcollection\b',
        r'\bbundle\b',
        r'\bmystery\s+box\b',
        r'\bmystery\s+pack\b',
        r'\bmixed\s+lot\b',
        r'\bbulk\b',
        r'\bmultiple\b',
        r'\bset\s+of\b',
        r'\bbox\s+of\b',
        r'\bpack\s+of\b',
    ]
    
    # Check if collection keywords appear with numbers
    for keyword in collection_keywords:
        if re.search(keyword, text_lower):
            # Check if there's also a number in the text
            if re.search(r'\b\d+\b', text_lower):
                return True
    
    # Pattern 3: Explicit ranges or lists
    # e.g., "1-10 cards", "5, 10, 15 cards"
    range_patterns = [
        r'\b\d+\s*-\s*\d+\b',                # "1-10", "5-20"
        r'\b\d+\s*,\s*\d+\b',                # "5, 10, 15"
    ]
    
    for pattern in range_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Pattern 4: Words like "each", "per", suggesting multiple items
    if re.search(r'\beach\b', text_lower) and re.search(r'\b\d+\b', text_lower):
        return True
    
    return False


def extract_grade_from_text(text: str, nlp=None) -> str:
    """
    Extract grade from text using NLP and pattern matching.
    
    Args:
        text: The card name or title text
        nlp: spaCy NLP model (optional)
    
    Returns:
        Extracted grade as string, or empty string if not found
    """
    if not text:
        return ""
    
    # Pattern 1: Direct grade patterns (e.g., "CGC 10", "PSA 9.5", "Grade 8")
    grade_patterns = [
        r'\b(?:CGC|PSA|BGS|SGC)\s*(\d+(?:\.\d+)?)\b',  # Company + grade
        r'\bgrade\s*(\d+(?:\.\d+)?)\b',  # "grade X"
        r'\bgraded\s*(\d+(?:\.\d+)?)\b',  # "graded X"
        r'\b(\d+(?:\.\d+)?)\s*(?:mint|nm|gem)\b',  # X MINT/NM/GEM
        r'\bgem\s*mint\s*(\d+(?:\.\d+)?)\b',  # GEM MINT X
        r'\bpristine\s*(\d+(?:\.\d+)?)\b',  # PRISTINE X
        r'\bmint\+?\s*(\d+(?:\.\d+)?)\b',  # MINT/MINT+ X
    ]
    
    for pattern in grade_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            grade = match.group(1)
            # Validate grade is in reasonable range (0-10)
            try:
                grade_float = float(grade)
                if 0 <= grade_float <= 10:
                    return grade
            except ValueError:
                continue
    
    # Pattern 2: Look for standalone numbers that might be grades
    # Common in titles like "Pokemon Card 10 CGC" or "9.5 Charizard"
    standalone_patterns = [
        r'\b(10|9\.5|9|8\.5|8|7\.5|7|6\.5|6|5\.5|5)\b'
    ]
    
    for pattern in standalone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # If we find a number in the valid grade range, use it
            return matches[0]
    
    # Pattern 3: Use spaCy NLP if available
    if nlp and SPACY_AVAILABLE:
        try:
            doc = nlp(text)
            # Look for numeric entities near grading-related words
            for i, token in enumerate(doc):
                if token.like_num:
                    # Check surrounding tokens for grading context
                    window_start = max(0, i - 2)
                    window_end = min(len(doc), i + 3)
                    context = " ".join([t.text for t in doc[window_start:window_end]]).lower()
                    
                    if any(word in context for word in ['cgc', 'psa', 'bgs', 'sgc', 'grade', 'mint', 'gem', 'pristine']):
                        try:
                            grade_val = float(token.text)
                            if 0 <= grade_val <= 10:
                                return token.text
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Warning: spaCy processing failed: {e}")
    
    return ""


def should_filter_row(row: Dict[str, str], nlp=None) -> Tuple[bool, str]:
    """
    Determine if a row should be filtered out.
    
    Returns:
        Tuple of (should_filter: bool, reason: str)
    """
    # Check 1: Image count
    images_str = row.get('images', '')
    image_count = count_images(images_str)
    if image_count <= 1:
        return True, f"Too few images ({image_count})"
    
    # Check 2: Contains "thicc"
    # Check in all relevant text fields
    text_fields = ['title', 'card_name']
    for field in text_fields:
        if contains_thicc(row.get(field, '')):
            return True, f"Contains 'thicc' in {field}"
    
    # Check 3: Multiple cards indicator (check BEFORE grade extraction)
    # This prevents misidentifying quantity numbers as grades
    title = row.get('title', '')
    card_name = row.get('card_name', '')
    
    if contains_multiple_cards(title) or contains_multiple_cards(card_name):
        return True, "Multiple cards listing detected"
    
    # Check 4: Missing grade with NLP extraction
    grade = row.get('grade', '').strip()
    if not grade:
        # Try to extract grade from card_name first, then title
        extracted_grade = extract_grade_from_text(card_name, nlp)
        if not extracted_grade:
            extracted_grade = extract_grade_from_text(title, nlp)
        
        if extracted_grade:
            # Update the row with extracted grade
            row['grade'] = extracted_grade
            return False, f"Grade extracted: {extracted_grade}"
        else:
            return True, "Missing grade and could not extract"
    
    return False, "Passed all filters"


def delete_image_files(images_str: str, base_dir: Path) -> int:
    """
    Delete image files listed in the images column and their containing directories.
    Each directory contains images from one listing, so we delete the entire directory.
    
    Args:
        images_str: Comma-separated list of image paths
        base_dir: Base directory where CSV is located
    
    Returns:
        Number of files successfully deleted
    """
    if not images_str or images_str.strip() == "":
        return 0
    
    deleted_count = 0
    directories_to_delete = set()
    images = [img.strip() for img in images_str.split(',') if img.strip()]
    
    # First, collect all unique directories and delete individual files
    for image_path in images:
        # Convert relative path to absolute path
        full_path = base_dir / "downloaded_images" / image_path
        
        if full_path.exists() and full_path.is_file():
            try:
                # Track the parent directory (the listing directory)
                parent_dir = full_path.parent
                directories_to_delete.add(parent_dir)
                
                full_path.unlink()
                deleted_count += 1
                print(f"  Deleted image: {image_path}")
            except Exception as e:
                print(f"  Warning: Could not delete {image_path}: {e}")
        else:
            # Even if file doesn't exist, track directory for cleanup
            parent_dir = (base_dir / "downloaded_images" / image_path).parent
            if parent_dir.exists():
                directories_to_delete.add(parent_dir)
    
    # Now delete the directories if they're empty or contain only the listing's files
    for directory in directories_to_delete:
        try:
            # Check if directory is empty or only contains files we've deleted
            remaining_files = list(directory.iterdir())
            
            if not remaining_files:
                # Directory is empty, safe to delete
                directory.rmdir()
                print(f"  Deleted directory: {directory.relative_to(base_dir / 'downloaded_images')}")
            else:
                # Directory still has files, just report it
                print(f"  Note: Directory still contains {len(remaining_files)} file(s): {directory.relative_to(base_dir / 'downloaded_images')}")
        except Exception as e:
            print(f"  Warning: Could not delete directory {directory.name}: {e}")
    
    return deleted_count


def filter_csv(input_file: str, output_file: str = None, delete_images: bool = True, use_nlp: bool = True):
    """
    Filter CSV file based on criteria and optionally delete associated images.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (default: input_file with '_filtered' suffix)
        delete_images: Whether to delete image files for filtered rows
        use_nlp: Whether to use spaCy NLP for grade extraction
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Determine output file path
    if output_file is None:
        output_path = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"
    else:
        output_path = Path(output_file)
    
    # Load spaCy model if available and requested
    nlp = None
    if use_nlp and SPACY_AVAILABLE:
        try:
            nlp = spacy.load("en_core_web_sm")
            print("Loaded spaCy model for NLP processing")
        except OSError:
            print("Warning: spaCy model 'en_core_web_sm' not found.")
            print("Install with: python -m spacy download en_core_web_sm")
            use_nlp = False
    
    # Process CSV
    base_dir = input_path.parent
    rows_kept = []
    rows_filtered = []
    stats = {
        'total': 0,
        'kept': 0,
        'filtered': 0,
        'images_deleted': 0,
        'grades_extracted': 0,
        'reasons': {}
    }
    
    print(f"\nProcessing: {input_file}")
    print(f"Output: {output_path}")
    print("-" * 60)
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        for row in reader:
            stats['total'] += 1
            should_filter, reason = should_filter_row(row, nlp)
            
            if should_filter:
                stats['filtered'] += 1
                stats['reasons'][reason] = stats['reasons'].get(reason, 0) + 1
                rows_filtered.append(row)
                
                print(f"Filtered row {stats['total']}: {row.get('card_name', 'N/A')[:50]} - {reason}")
                
                # Delete associated images if requested
                if delete_images:
                    deleted = delete_image_files(row.get('images', ''), base_dir)
                    stats['images_deleted'] += deleted
            else:
                stats['kept'] += 1
                rows_kept.append(row)
                
                # Track if grade was extracted
                if "extracted" in reason.lower():
                    stats['grades_extracted'] += 1
                    print(f"Row {stats['total']}: {row.get('card_name', 'N/A')[:50]} - {reason}")
    
    # Write filtered results
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_kept)
    
    # Print summary
    print("\n" + "=" * 60)
    print("FILTERING SUMMARY")
    print("=" * 60)
    print(f"Total rows processed: {stats['total']}")
    print(f"Rows kept: {stats['kept']}")
    print(f"Rows filtered: {stats['filtered']}")
    print(f"Grades extracted via NLP: {stats['grades_extracted']}")
    if delete_images:
        print(f"Image files deleted: {stats['images_deleted']}")
    
    print("\nFilter reasons:")
    for reason, count in sorted(stats['reasons'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {reason}: {count}")
    
    print(f"\nFiltered data saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter Pokemon card CSV data based on images, text content, and grades.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Filter a CSV file (creates output with _filtered suffix)
  python filter.py input.csv
  
  # Specify custom output file
  python filter.py input.csv -o output.csv
  
  # Keep images (don't delete them)
  python filter.py input.csv --no-delete-images
  
  # Skip NLP processing
  python filter.py input.csv --no-nlp
        """
    )
    
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: input_filtered.csv)')
    parser.add_argument('--no-delete-images', action='store_true', 
                        help='Do not delete image files for filtered rows')
    parser.add_argument('--no-nlp', action='store_true',
                        help='Skip NLP processing for grade extraction')
    
    args = parser.parse_args()
    
    filter_csv(
        input_file=args.input_file,
        output_file=args.output,
        delete_images=not args.no_delete_images,
        use_nlp=not args.no_nlp
    )


if __name__ == "__main__":
    main()
