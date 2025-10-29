#!/usr/bin/env python3
"""
Utility functions for converting scraper JSON output to CSV format.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Union, List, Dict
import logging

logger = logging.getLogger(__name__)


def json_to_csv(json_path: Union[str, Path], csv_path: Union[str, Path] = None, 
                flatten_images: bool = True) -> str:
    """
    Convert JSON output from scraper to CSV format.
    
    Args:
        json_path: Path to the JSON file
        csv_path: Path for the output CSV file (optional, defaults to same name with .csv)
        flatten_images: If True, flatten image_urls and images lists into comma-separated strings
        
    Returns:
        Path to the created CSV file
        
    Example:
        >>> json_to_csv('output.json')
        'output.csv'
        >>> json_to_csv('output.json', 'cards.csv')
        'cards.csv'
    """
    json_path = Path(json_path)
    
    if csv_path is None:
        csv_path = json_path.with_suffix('.csv')
    else:
        csv_path = Path(csv_path)
    
    logger.info(f"Converting {json_path} to CSV format")
    
    # Load JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        raise
    
    if not data:
        logger.warning(f"No data found in {json_path}")
        # Create empty CSV with headers
        df = pd.DataFrame(columns=['title', 'card_name', 'grading_company', 'grade', 
                                   'price', 'listing_url', 'image_urls', 'source', 
                                   'scraped_date', 'images'])
        df.to_csv(csv_path, index=False)
        return str(csv_path)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Flatten list columns if requested
    if flatten_images:
        if 'image_urls' in df.columns:
            df['image_urls'] = df['image_urls'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )
        if 'images' in df.columns:
            df['images'] = df['images'].apply(
                lambda x: ', '.join([img if isinstance(img, str) else img.get('path', '') 
                                    for img in x]) if isinstance(x, list) else x
            )
    
    # Save to CSV
    df.to_csv(csv_path, index=False, encoding='utf-8')
    logger.info(f"Saved CSV with {len(df)} rows to {csv_path}")
    
    return str(csv_path)


def json_to_csv_with_stats(json_path: Union[str, Path], csv_path: Union[str, Path] = None,
                           stats_path: Union[str, Path] = None) -> Dict[str, str]:
    """
    Convert JSON to CSV and generate a statistics summary.
    
    Args:
        json_path: Path to the JSON file
        csv_path: Path for the output CSV file (optional)
        stats_path: Path for the statistics text file (optional)
        
    Returns:
        Dictionary with paths to created files
        
    Example:
        >>> result = json_to_csv_with_stats('output.json')
        >>> print(result)
        {'csv': 'output.csv', 'stats': 'output_stats.txt'}
    """
    json_path = Path(json_path)
    
    if csv_path is None:
        csv_path = json_path.with_suffix('.csv')
    else:
        csv_path = Path(csv_path)
    
    if stats_path is None:
        stats_path = json_path.with_name(f"{json_path.stem}_stats.txt")
    else:
        stats_path = Path(stats_path)
    
    # Convert to CSV first
    csv_result = json_to_csv(json_path, csv_path)
    
    # Load data for statistics
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Generate statistics
    stats = []
    stats.append("=" * 60)
    stats.append(f"GRADED CARDS SCRAPER STATISTICS")
    stats.append(f"Generated from: {json_path.name}")
    stats.append("=" * 60)
    stats.append("")
    
    # Basic counts
    stats.append(f"Total Items Scraped: {len(df)}")
    stats.append("")
    
    # Grading company breakdown
    if 'grading_company' in df.columns:
        stats.append("Items by Grading Company:")
        company_counts = df['grading_company'].value_counts()
        for company, count in company_counts.items():
            stats.append(f"  {company}: {count}")
        stats.append("")
    
    # Grade breakdown
    if 'grade' in df.columns:
        stats.append("Items by Grade:")
        grade_counts = df['grade'].value_counts().sort_index()
        for grade, count in grade_counts.items():
            stats.append(f"  Grade {grade}: {count}")
        stats.append("")
    
    # Price statistics
    if 'price' in df.columns:
        prices = df['price'].dropna()
        if len(prices) > 0:
            stats.append("Price Statistics:")
            stats.append(f"  Items with prices: {len(prices)}/{len(df)}")
            stats.append(f"  Average Price: ${prices.mean():.2f}")
            stats.append(f"  Median Price: ${prices.median():.2f}")
            stats.append(f"  Min Price: ${prices.min():.2f}")
            stats.append(f"  Max Price: ${prices.max():.2f}")
            stats.append(f"  Total Value: ${prices.sum():.2f}")
            stats.append("")
    
    # Price by grading company
    if 'price' in df.columns and 'grading_company' in df.columns:
        stats.append("Average Price by Grading Company:")
        avg_prices = df.groupby('grading_company')['price'].mean().sort_values(ascending=False)
        for company, avg_price in avg_prices.items():
            if pd.notna(avg_price):
                stats.append(f"  {company}: ${avg_price:.2f}")
        stats.append("")
    
    # Price by grade
    if 'price' in df.columns and 'grade' in df.columns:
        stats.append("Average Price by Grade:")
        avg_prices = df.groupby('grade')['price'].mean().sort_index()
        for grade, avg_price in avg_prices.items():
            if pd.notna(avg_price):
                stats.append(f"  Grade {grade}: ${avg_price:.2f}")
        stats.append("")
    
    # Image statistics
    if 'images' in df.columns:
        images_downloaded = df['images'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
        stats.append(f"Images Downloaded: {images_downloaded}")
        stats.append("")
    
    # Source breakdown
    if 'source' in df.columns:
        stats.append("Items by Source:")
        source_counts = df['source'].value_counts()
        for source, count in source_counts.items():
            stats.append(f"  {source}: {count}")
        stats.append("")
    
    # Top 10 most expensive cards
    if 'price' in df.columns and 'title' in df.columns:
        top_cards = df.nlargest(10, 'price')[['title', 'price', 'grading_company', 'grade']]
        if len(top_cards) > 0:
            stats.append("Top 10 Most Expensive Cards:")
            for idx, row in top_cards.iterrows():
                company = row['grading_company'] if pd.notna(row['grading_company']) else 'N/A'
                grade = row['grade'] if pd.notna(row['grade']) else 'N/A'
                price = row['price'] if pd.notna(row['price']) else 0
                title = row['title'][:60] + '...' if len(row['title']) > 60 else row['title']
                stats.append(f"  ${price:.2f} - {title} ({company} {grade})")
            stats.append("")
    
    stats.append("=" * 60)
    
    # Write statistics to file
    stats_text = '\n'.join(stats)
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(stats_text)
    
    logger.info(f"Saved statistics to {stats_path}")
    print(stats_text)  # Also print to console
    
    return {
        'csv': str(csv_path),
        'stats': str(stats_path)
    }


def batch_json_to_csv(json_dir: Union[str, Path], output_dir: Union[str, Path] = None) -> List[str]:
    """
    Convert all JSON files in a directory to CSV format.
    
    Args:
        json_dir: Directory containing JSON files
        output_dir: Directory for output CSV files (optional, defaults to same directory)
        
    Returns:
        List of paths to created CSV files
        
    Example:
        >>> csv_files = batch_json_to_csv('scraped_data/')
        >>> print(f"Converted {len(csv_files)} files")
    """
    json_dir = Path(json_dir)
    output_dir = Path(output_dir) if output_dir else json_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_files = list(json_dir.glob('*.json'))
    csv_files = []
    
    logger.info(f"Converting {len(json_files)} JSON files to CSV")
    
    for json_file in json_files:
        csv_file = output_dir / json_file.with_suffix('.csv').name
        try:
            json_to_csv(json_file, csv_file)
            csv_files.append(str(csv_file))
        except Exception as e:
            logger.error(f"Failed to convert {json_file}: {e}")
    
    logger.info(f"Successfully converted {len(csv_files)}/{len(json_files)} files")
    return csv_files


def merge_csv_files(csv_files: List[Union[str, Path]], output_path: Union[str, Path],
                    remove_duplicates: bool = True) -> str:
    """
    Merge multiple CSV files into one.
    
    Args:
        csv_files: List of CSV file paths to merge
        output_path: Path for the merged CSV file
        remove_duplicates: If True, remove duplicate rows based on listing_url
        
    Returns:
        Path to the merged CSV file
        
    Example:
        >>> merged = merge_csv_files(['output1.csv', 'output2.csv'], 'all_cards.csv')
    """
    output_path = Path(output_path)
    
    logger.info(f"Merging {len(csv_files)} CSV files")
    
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to read {csv_file}: {e}")
    
    if not dfs:
        logger.error("No CSV files could be loaded")
        raise ValueError("No valid CSV files to merge")
    
    # Merge all dataframes
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Remove duplicates if requested
    if remove_duplicates and 'listing_url' in merged_df.columns:
        original_len = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['listing_url'], keep='first')
        logger.info(f"Removed {original_len - len(merged_df)} duplicate entries")
    
    # Save merged file
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged CSV with {len(merged_df)} rows to {output_path}")
    
    return str(output_path)
