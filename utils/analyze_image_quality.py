#!/usr/bin/env python3
"""
Analyze image quality and dimensions from scraped card images.
Useful for verifying high-resolution downloads before AI training.
"""

import os
import sys
from pathlib import Path
from PIL import Image
from collections import defaultdict
import json


def analyze_image_quality(directory='downloaded_images'):
    """
    Analyze all images in the directory and provide quality statistics.
    
    Args:
        directory: Path to the downloaded_images directory
        
    Returns:
        dict: Statistics about image quality
    """
    stats = {
        'total': 0,
        'high_res': 0,      # >= 1200px
        'medium': 0,        # >= 800px
        'acceptable': 0,    # >= 400px
        'low': 0,           # < 400px
        'by_source': defaultdict(lambda: {'count': 0, 'avg_width': 0, 'avg_height': 0}),
        'by_company': defaultdict(lambda: {'count': 0, 'avg_width': 0, 'avg_height': 0}),
        'dimensions': [],
        'failed': []
    }
    
    directory = Path(directory)
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return stats
    
    print(f"🔍 Analyzing images in: {directory}")
    print("=" * 60)
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                path = os.path.join(root, file)
                
                try:
                    with Image.open(path) as img:
                        width, height = img.size
                        min_dim = min(width, height)
                        
                        stats['total'] += 1
                        stats['dimensions'].append((width, height, path))
                        
                        # Categorize by quality
                        if min_dim >= 1200:
                            stats['high_res'] += 1
                            quality = 'HIGH'
                        elif min_dim >= 800:
                            stats['medium'] += 1
                            quality = 'MEDIUM'
                        elif min_dim >= 400:
                            stats['acceptable'] += 1
                            quality = 'ACCEPTABLE'
                        else:
                            stats['low'] += 1
                            quality = 'LOW'
                        
                        # Extract source and company from path
                        parts = Path(path).parts
                        if len(parts) >= 2:
                            source = parts[-3] if len(parts) >= 3 else 'unknown'
                            company = parts[-2]
                            
                            stats['by_source'][source]['count'] += 1
                            stats['by_source'][source]['avg_width'] += width
                            stats['by_source'][source]['avg_height'] += height
                            
                            stats['by_company'][company]['count'] += 1
                            stats['by_company'][company]['avg_width'] += width
                            stats['by_company'][company]['avg_height'] += height
                        
                        # Print individual file info if low quality
                        if quality == 'LOW':
                            print(f"⚠️  {quality}: {width}x{height}px - {Path(path).name}")
                        
                except Exception as e:
                    stats['failed'].append((path, str(e)))
                    print(f"❌ Failed to process: {file} - {e}")
    
    # Calculate averages
    for source in stats['by_source']:
        count = stats['by_source'][source]['count']
        stats['by_source'][source]['avg_width'] = int(stats['by_source'][source]['avg_width'] / count)
        stats['by_source'][source]['avg_height'] = int(stats['by_source'][source]['avg_height'] / count)
    
    for company in stats['by_company']:
        count = stats['by_company'][company]['count']
        stats['by_company'][company]['avg_width'] = int(stats['by_company'][company]['avg_width'] / count)
        stats['by_company'][company]['avg_height'] = int(stats['by_company'][company]['avg_height'] / count)
    
    return stats


def print_statistics(stats):
    """Print formatted statistics"""
    total = stats['total']
    
    if total == 0:
        print("📭 No images found to analyze.")
        return
    
    print("\n" + "=" * 60)
    print("📊 IMAGE QUALITY ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n📁 Total Images: {total}")
    print(f"\n🎯 Quality Distribution:")
    print(f"   🏆 High Resolution (≥1200px):  {stats['high_res']:4d} ({stats['high_res']/total*100:5.1f}%)")
    print(f"   ⭐ Medium (≥800px):            {stats['medium']:4d} ({stats['medium']/total*100:5.1f}%)")
    print(f"   ✅ Acceptable (≥400px):        {stats['acceptable']:4d} ({stats['acceptable']/total*100:5.1f}%)")
    print(f"   ⚠️  Low (<400px):              {stats['low']:4d} ({stats['low']/total*100:5.1f}%)")
    
    # AI Training Readiness
    suitable_for_training = stats['high_res'] + stats['medium'] + stats['acceptable']
    print(f"\n🤖 AI Training Readiness:")
    print(f"   Suitable images (≥400px): {suitable_for_training} ({suitable_for_training/total*100:.1f}%)")
    
    if stats['high_res'] / total >= 0.7:
        print(f"   Status: ✅ EXCELLENT - Majority high-resolution images")
    elif suitable_for_training / total >= 0.8:
        print(f"   Status: ✅ GOOD - Most images suitable for training")
    elif suitable_for_training / total >= 0.6:
        print(f"   Status: ⚠️ FAIR - Consider filtering low-quality images")
    else:
        print(f"   Status: ❌ POOR - Many low-quality images, increase minimum resolution")
    
    # By Source
    if stats['by_source']:
        print(f"\n🌐 By Marketplace:")
        for source, data in sorted(stats['by_source'].items()):
            print(f"   {source.upper():12s}: {data['count']:4d} images (avg: {data['avg_width']}x{data['avg_height']}px)")
    
    # By Company
    if stats['by_company']:
        print(f"\n🏢 By Grading Company:")
        for company, data in sorted(stats['by_company'].items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"   {company:12s}: {data['count']:4d} images (avg: {data['avg_width']}x{data['avg_height']}px)")
    
    # Dimension Stats
    if stats['dimensions']:
        widths = [d[0] for d in stats['dimensions']]
        heights = [d[1] for d in stats['dimensions']]
        
        print(f"\n📏 Dimension Statistics:")
        print(f"   Average:   {sum(widths)//len(widths)}x{sum(heights)//len(heights)}px")
        print(f"   Maximum:   {max(widths)}x{max(heights)}px")
        print(f"   Minimum:   {min(widths)}x{min(heights)}px")
        
        # Show smallest images
        smallest = sorted(stats['dimensions'], key=lambda x: min(x[0], x[1]))[:3]
        if smallest:
            print(f"\n   ⚠️  Smallest images:")
            for width, height, path in smallest:
                print(f"      {width}x{height}px - {Path(path).name}")
    
    # Failed images
    if stats['failed']:
        print(f"\n❌ Failed to Process: {len(stats['failed'])}")
        for path, error in stats['failed'][:5]:
            print(f"   {Path(path).name}: {error}")
    
    print("\n" + "=" * 60)


def export_to_json(stats, output_file='image_quality_report.json'):
    """Export statistics to JSON file"""
    # Convert defaultdict to regular dict and remove image paths for cleaner export
    export_data = {
        'summary': {
            'total': stats['total'],
            'high_res': stats['high_res'],
            'medium': stats['medium'],
            'acceptable': stats['acceptable'],
            'low': stats['low'],
        },
        'by_source': dict(stats['by_source']),
        'by_company': dict(stats['by_company']),
        'failed_count': len(stats['failed'])
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n💾 Detailed report exported to: {output_file}")


def main():
    """Main function"""
    directory = sys.argv[1] if len(sys.argv) > 1 else 'downloaded_images'
    
    print("🖼️  Card Image Quality Analyzer")
    print("=" * 60)
    print("For AI model training preparation\n")
    
    stats = analyze_image_quality(directory)
    print_statistics(stats)
    
    # Export to JSON
    if stats['total'] > 0:
        export_to_json(stats)
        
        # Recommendations
        print("\n💡 Recommendations:")
        if stats['low'] > stats['total'] * 0.2:
            print("   • Consider increasing IMAGES_MIN_HEIGHT/WIDTH to filter low-quality images")
            print("   • Or scrape from sources with better image quality")
        
        if stats['high_res'] > stats['total'] * 0.7:
            print("   • ✅ Image quality is excellent for AI training!")
            print("   • Dataset is ready for preprocessing and model training")
        
        print("\n📚 Next steps:")
        print("   1. Review LOW quality images and decide if they should be filtered")
        print("   2. Organize images by grade for supervised learning")
        print("   3. Split into training (80%) and validation (20%) sets")
        print("   4. Apply preprocessing: resize, normalize, augment")
        print("   5. Train your card grading model!")


if __name__ == "__main__":
    main()
