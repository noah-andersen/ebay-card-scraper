#!/bin/bash

################################################################################
# eBay Card Scraper Batch Job Script
# 
# This script runs multiple scraping jobs with different search queries,
# appends all results to the same output files, and then filters the data.
#
# Usage: ./job.sh
################################################################################

set -e  # Exit on error

# Configuration
OUTPUT_DIR="cgc_pokemon_low_grades"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_JSON="${OUTPUT_DIR}/batch_job_${TIMESTAMP}.json"
OUTPUT_CSV="${OUTPUT_DIR}/batch_job_${TIMESTAMP}.csv"
FILTERED_CSV="${OUTPUT_DIR}/batch_job_${TIMESTAMP}_filtered.csv"
STATS_FILE="${OUTPUT_DIR}/batch_job_${TIMESTAMP}_stats.txt"

# Scraper settings
SOURCE="ebay"  # Change to "mercari" if needed
SPIDER_NAME="${SOURCE}_graded_cards"
MAX_PAGES=2  # Pages per search query
DOWNLOAD_IMAGES=True
DELETE_FILTERED_IMAGES=True
USE_NLP=True

# Search queries - Add or modify as needed
SEARCH_QUERIES=(
    "CGC 1 Magic The Gathering"
    "CGC 2 Magic The Gathering"
    "CGC 3 Magic The Gathering"
    "CGC 4 Magic The Gathering"
    "CGC 5 Magic The Gathering"
    "CGC 6 Magic The Gathering"
)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
    echo ""
}

################################################################################
# Main Script
################################################################################

print_header "eBay Card Scraper - Batch Job Started"

log_info "Job started at: $(date)"
log_info "Output JSON: ${OUTPUT_JSON}"
log_info "Output CSV: ${OUTPUT_CSV}"
log_info "Total search queries: ${#SEARCH_QUERIES[@]}"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Initialize temporary JSON array file
TEMP_JSON_DIR="${OUTPUT_DIR}/temp_${TIMESTAMP}"
mkdir -p "${TEMP_JSON_DIR}"

echo "[]" > "${OUTPUT_JSON}"

# Counter for tracking progress
QUERY_NUM=0
TOTAL_QUERIES=${#SEARCH_QUERIES[@]}
SUCCESSFUL_SCRAPES=0
FAILED_SCRAPES=0

# Loop through each search query
for QUERY in "${SEARCH_QUERIES[@]}"; do
    QUERY_NUM=$((QUERY_NUM + 1))
    
    print_header "Query ${QUERY_NUM}/${TOTAL_QUERIES}: ${QUERY}"
    
    # Create temporary output file for this query
    TEMP_OUTPUT="${TEMP_JSON_DIR}/query_${QUERY_NUM}.json"
    
    log_info "Running scraper..."
    
    # Run scrapy spider
    if scrapy crawl "${SPIDER_NAME}" \
        -a "search_query=${QUERY}" \
        -a "max_pages=${MAX_PAGES}" \
        -O "${TEMP_OUTPUT}" \
        2>&1 | tee "${TEMP_JSON_DIR}/query_${QUERY_NUM}.log"; then
        
        log_success "Scraping completed for: ${QUERY}"
        SUCCESSFUL_SCRAPES=$((SUCCESSFUL_SCRAPES + 1))
        
        # Check if temp file has data
        if [ -f "${TEMP_OUTPUT}" ] && [ -s "${TEMP_OUTPUT}" ]; then
            log_info "Appending results to main JSON file..."
            
            # Merge JSON files using Python
            python3 << EOF
import json

# Read existing data
with open("${OUTPUT_JSON}", 'r') as f:
    existing_data = json.load(f)

# Read new data
try:
    with open("${TEMP_OUTPUT}", 'r') as f:
        new_data = json.load(f)
    
    # Ensure new_data is a list
    if isinstance(new_data, dict):
        new_data = [new_data]
    
    # Append new data
    existing_data.extend(new_data)
    
    # Write combined data back
    with open("${OUTPUT_JSON}", 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"Added {len(new_data)} items to output file")
except Exception as e:
    print(f"Error merging JSON: {e}")
    exit(1)
EOF
            
        else
            log_warning "No data found for query: ${QUERY}"
        fi
    else
        log_error "Scraping failed for: ${QUERY}"
        FAILED_SCRAPES=$((FAILED_SCRAPES + 1))
    fi
    
    # Small delay between queries to be respectful
    if [ ${QUERY_NUM} -lt ${TOTAL_QUERIES} ]; then
        log_info "Waiting 5 seconds before next query..."
        sleep 5
    fi
done

print_header "Scraping Phase Complete"

log_info "Successful scrapes: ${SUCCESSFUL_SCRAPES}/${TOTAL_QUERIES}"
log_info "Failed scrapes: ${FAILED_SCRAPES}/${TOTAL_QUERIES}"

# Check if we have any data
ITEM_COUNT=$(python3 -c "import json; print(len(json.load(open('${OUTPUT_JSON}'))))")
log_info "Total items scraped: ${ITEM_COUNT}"

if [ "${ITEM_COUNT}" -eq "0" ]; then
    log_error "No data was scraped. Exiting."
    exit 1
fi

################################################################################
# Convert to CSV
################################################################################

print_header "Converting JSON to CSV with Statistics"

log_info "Running conversion..."

python3 << EOF
import sys
sys.path.insert(0, '.')
from utils.convert_to_csv import json_to_csv_with_stats

try:
    result = json_to_csv_with_stats("${OUTPUT_JSON}")
    print(f"CSV file: {result['csv']}")
    print(f"Stats file: {result['stats']}")
except Exception as e:
    print(f"Error during conversion: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    log_success "CSV conversion completed"
    # The function creates CSV with same name as JSON but .csv extension
    OUTPUT_CSV="${OUTPUT_JSON%.json}.csv"
else
    log_error "CSV conversion failed"
    exit 1
fi

################################################################################
# Filter Data
################################################################################

print_header "Filtering Data"

log_info "Running filter with NLP grade extraction..."
log_info "Delete filtered images: ${DELETE_FILTERED_IMAGES}"

python3 << EOF
import sys
sys.path.insert(0, '.')
from utils.filter import filter_csv

try:
    filter_csv(
        input_file="${OUTPUT_CSV}",
        output_file="${FILTERED_CSV}",
        delete_images=${DELETE_FILTERED_IMAGES},
        use_nlp=${USE_NLP}
    )
    print("Filtering completed successfully")
except Exception as e:
    print(f"Error during filtering: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    log_success "Data filtering completed"
    log_info "Filtered CSV: ${FILTERED_CSV}"
else
    log_error "Filtering failed"
fi

################################################################################
# Cleanup and Summary
################################################################################

print_header "Job Summary"

# Clean up temporary files
log_info "Cleaning up temporary files..."
rm -rf "${TEMP_JSON_DIR}"

# Count final results
ORIGINAL_COUNT=$(wc -l < "${OUTPUT_CSV}" | tr -d ' ')
ORIGINAL_COUNT=$((ORIGINAL_COUNT - 1))  # Subtract header row

if [ -f "${FILTERED_CSV}" ]; then
    FILTERED_COUNT=$(wc -l < "${FILTERED_CSV}" | tr -d ' ')
    FILTERED_COUNT=$((FILTERED_COUNT - 1))  # Subtract header row
    REMOVED_COUNT=$((ORIGINAL_COUNT - FILTERED_COUNT))
else
    FILTERED_COUNT=0
    REMOVED_COUNT=0
fi

# Print summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        JOB COMPLETED                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📊 Statistics:"
echo "    • Search queries processed:  ${SUCCESSFUL_SCRAPES}/${TOTAL_QUERIES}"
echo "    • Total items scraped:       ${ITEM_COUNT}"
echo "    • Items after filtering:     ${FILTERED_COUNT}"
echo "    • Items removed:             ${REMOVED_COUNT}"
echo ""
echo "  📁 Output Files:"
echo "    • JSON:          ${OUTPUT_JSON}"
echo "    • CSV:           ${OUTPUT_CSV}"
echo "    • Filtered CSV:  ${FILTERED_CSV}"
echo ""
echo "  ⏱️  Job completed at: $(date)"
echo ""

log_success "Batch job completed successfully!"

exit 0
