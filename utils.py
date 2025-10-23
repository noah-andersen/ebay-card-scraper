"""
Utility functions for eBay card scraper.
"""

import os
import re
from typing import List, Dict
import pandas as pd


def clean_card_name(name: str) -> str:
    """
    Clean and normalize card name.
    
    Args:
        name: Raw card name from listing
        
    Returns:
        Cleaned card name
    """
    # Remove grading info
    name = re.sub(r'(PSA|BGS|CGC)\s*\d+(\.\d+)?', '', name, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def extract_grade_from_title(title: str) -> tuple:
    """
    Extract grading company and grade from listing title.
    
    Args:
        title: Listing title
        
    Returns:
        Tuple of (grading_company, grade) or (None, None)
    """
    # PSA pattern
    psa_match = re.search(r'PSA\s*(\d+(\.\d+)?)', title, re.IGNORECASE)
    if psa_match:
        return ('PSA', float(psa_match.group(1)))
    
    # BGS pattern
    bgs_match = re.search(r'BGS\s*(\d+(\.\d+)?)', title, re.IGNORECASE)
    if bgs_match:
        return ('BGS', float(bgs_match.group(1)))
    
    # CGC pattern
    cgc_match = re.search(r'CGC\s*(\d+(\.\d+)?)', title, re.IGNORECASE)
    if cgc_match:
        return ('CGC', float(cgc_match.group(1)))
    
    return (None, None)


def load_metadata(filepath: str) -> pd.DataFrame:
    """
    Load metadata from CSV file.
    
    Args:
        filepath: Path to metadata CSV
        
    Returns:
        DataFrame with metadata
    """
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()


def get_statistics(metadata_file: str) -> Dict:
    """
    Get statistics from scraped data.
    
    Args:
        metadata_file: Path to metadata CSV
        
    Returns:
        Dictionary with statistics
    """
    if not os.path.exists(metadata_file):
        return {'total_cards': 0}
    
    df = pd.read_csv(metadata_file)
    
    stats = {
        'total_cards': len(df),
        'by_company': df['grading_company'].value_counts().to_dict(),
        'by_grade': df.groupby(['grading_company', 'grade']).size().to_dict(),
        'avg_price_by_grade': df.groupby(['grading_company', 'grade'])['price'].mean().to_dict(),
        'unique_cards': df['card_name'].nunique()
    }
    
    return stats


def print_statistics(metadata_file: str):
    """
    Print statistics about scraped data.
    
    Args:
        metadata_file: Path to metadata CSV
    """
    stats = get_statistics(metadata_file)
    
    print("\n" + "="*60)
    print("SCRAPING STATISTICS")
    print("="*60)
    print(f"Total Cards: {stats['total_cards']}")
    print(f"Unique Card Names: {stats.get('unique_cards', 0)}")
    
    if 'by_company' in stats:
        print("\nBy Grading Company:")
        for company, count in stats['by_company'].items():
            print(f"  {company}: {count}")
    
    print("="*60 + "\n")


def deduplicate_images(images_dir: str, metadata_file: str):
    """
    Remove duplicate images based on listing ID.
    
    Args:
        images_dir: Directory containing images
        metadata_file: Path to metadata CSV
    """
    if not os.path.exists(metadata_file):
        print("No metadata file found")
        return
    
    df = pd.read_csv(metadata_file)
    
    # Find duplicates
    duplicates = df[df.duplicated(subset=['listing_id'], keep='first')]
    
    if len(duplicates) == 0:
        print("No duplicates found")
        return
    
    print(f"Found {len(duplicates)} duplicate listings")
    
    removed_count = 0
    for _, row in duplicates.iterrows():
        image_path = row['image_path']
        if os.path.exists(image_path):
            os.remove(image_path)
            removed_count += 1
            print(f"Removed: {image_path}")
    
    # Remove from metadata
    df = df.drop_duplicates(subset=['listing_id'], keep='first')
    df.to_csv(metadata_file, index=False)
    
    print(f"\nRemoved {removed_count} duplicate images")
    print(f"Updated metadata with {len(df)} unique records")


if __name__ == '__main__':
    # Example usage
    import config
    print_statistics(config.METADATA_FILE)
