#!/bin/bash

################################################################################
# Graded Cards Scraping Job Script
# 
# This script automates scraping of graded Pokemon cards from eBay and Mercari
# with configurable parameters and random delays between runs.
#
# Usage:
#   ./job.sh [options]
#
# Options:
#   -s, --source        Source to scrape: ebay, mercari, or both (default: both)
#   -c, --companies     Comma-separated list of grading companies (default: PSA,CGC,TAG)
#   -g, --grades        Comma-separated list of grades (default: 10,9,8,7,6,5,4,3,2,1)
#   -p, --pages         Maximum pages per search (default: 1)
#   -i, --items         Maximum items per search (default: 50)
#   -d, --min-delay     Minimum delay between runs in seconds (default: 10)
#   -D, --max-delay     Maximum delay between runs in seconds (default: 30)
#   -o, --output-dir    Output directory for scraped data (default: scraped_data)
#   -l, --log-dir       Log directory (default: logs)
#   -h, --help          Show this help message
#
# Examples:
#   ./job.sh                                    # Run with defaults
#   ./job.sh -s ebay -c "PSA,BGS" -g "10,9"     # eBay only, PSA & BGS, grades 10 & 9
#   ./job.sh -i 100 -d 30 -D 60                 # 100 items per search, 30-60s delay
#
################################################################################

set -e  # Exit on error

################################################################################
# Configuration Variables
################################################################################

# Default sources
SOURCES="both"  # Options: ebay, mercari, both

# Default grading companies
GRADING_COMPANIES=("PSA" "CGC" "TAG" "BGS" "SGC" "Beckett")

# Default grade levels
GRADES=("10" "9" "8" "7" "6" "5" "4" "3" "2" "1")

# Scraping parameters
MAX_PAGES=1
MAX_ITEMS_PER_SEARCH=50

# Delay parameters (in seconds)
MIN_DELAY=10
MAX_DELAY=30

# Output directories
OUTPUT_DIR="scraped_data"
LOG_DIR="logs"
IMAGE_DIR="downloaded_images"

# Timestamp format
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help message
show_help() {
    head -n 32 "$0" | tail -n 31 | sed 's/^# //'
    exit 0
}

# Generate random delay between min and max
random_delay() {
    local min=$1
    local max=$2
    echo $(( RANDOM % (max - min + 1) + min ))
}

# Create necessary directories
setup_directories() {
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$IMAGE_DIR"
    print_success "Directories created/verified"
}

# Check if scrapy is installed
check_dependencies() {
    if ! command -v scrapy &> /dev/null; then
        print_error "Scrapy is not installed. Please install it first:"
        echo "  pip install scrapy scrapy-playwright"
        exit 1
    fi
    print_success "Dependencies verified"
}

################################################################################
# Argument Parsing
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--source)
            SOURCES="$2"
            shift 2
            ;;
        -c|--companies)
            IFS=',' read -ra GRADING_COMPANIES <<< "$2"
            shift 2
            ;;
        -g|--grades)
            IFS=',' read -ra GRADES <<< "$2"
            shift 2
            ;;
        -p|--pages)
            MAX_PAGES="$2"
            shift 2
            ;;
        -i|--items)
            MAX_ITEMS_PER_SEARCH="$2"
            shift 2
            ;;
        -d|--min-delay)
            MIN_DELAY="$2"
            shift 2
            ;;
        -D|--max-delay)
            MAX_DELAY="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            ;;
    esac
done

################################################################################
# Main Script
################################################################################

print_info "=========================================="
print_info "Graded Cards Scraping Job"
print_info "Started at: $(date)"
print_info "=========================================="

# Check dependencies
check_dependencies

# Setup directories
setup_directories

# Display configuration
print_info "Configuration:"
echo "  Sources: $SOURCES"
echo "  Companies: ${GRADING_COMPANIES[*]}"
echo "  Grades: ${GRADES[*]}"
echo "  Max Pages: $MAX_PAGES"
echo "  Max Items: $MAX_ITEMS_PER_SEARCH"
echo "  Delay Range: ${MIN_DELAY}-${MAX_DELAY} seconds"
echo "  Output Dir: $OUTPUT_DIR"
echo "  Log Dir: $LOG_DIR"
echo ""

# Counters
TOTAL_JOBS=0
SUCCESSFUL_JOBS=0
FAILED_JOBS=0

# Determine which spiders to run
SPIDERS=()
if [[ "$SOURCES" == "both" ]]; then
    SPIDERS=("ebay_graded_cards" "mercari_graded_cards")
elif [[ "$SOURCES" == "ebay" ]]; then
    SPIDERS=("ebay_graded_cards")
elif [[ "$SOURCES" == "mercari" ]]; then
    SPIDERS=("mercari_graded_cards")
else
    print_error "Invalid source: $SOURCES. Must be 'ebay', 'mercari', or 'both'"
    exit 1
fi

################################################################################
# Scraping Loop
################################################################################

for spider in "${SPIDERS[@]}"; do
    # Determine source name for output files
    if [[ "$spider" == "ebay_graded_cards" ]]; then
        SOURCE_NAME="ebay"
    else
        SOURCE_NAME="mercari"
    fi
    
    print_info "=========================================="
    print_info "Running ${SOURCE_NAME} spider"
    print_info "=========================================="
    
    for company in "${GRADING_COMPANIES[@]}"; do
        for grade in "${GRADES[@]}"; do
            TOTAL_JOBS=$((TOTAL_JOBS + 1))
            
            # Build search query
            SEARCH_QUERY="Graded Pokemon cards ${company} ${grade}"
            
            # Build output filename
            OUTPUT_FILE="${OUTPUT_DIR}/${SOURCE_NAME}_${company}_grade${grade}_${TIMESTAMP}.json"
            LOG_FILE="${LOG_DIR}/${SOURCE_NAME}_${company}_grade${grade}_${TIMESTAMP}.log"
            
            print_info "Job ${TOTAL_JOBS}: Scraping ${SOURCE_NAME} - ${company} Grade ${grade}"
            echo "  Query: ${SEARCH_QUERY}"
            echo "  Output: ${OUTPUT_FILE}"
            
            # Run scrapy command
            if scrapy crawl "$spider" \
                -a search_query="$SEARCH_QUERY" \
                -a max_pages="$MAX_PAGES" \
                -s CLOSESPIDER_ITEMCOUNT="$MAX_ITEMS_PER_SEARCH" \
                -O "$OUTPUT_FILE" \
                > "$LOG_FILE" 2>&1; then
                
                print_success "Completed: ${company} Grade ${grade}"
                SUCCESSFUL_JOBS=$((SUCCESSFUL_JOBS + 1))
                
                # Check if any items were scraped
                if [[ -f "$OUTPUT_FILE" ]]; then
                    ITEM_COUNT=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(len(data))" 2>/dev/null || echo "0")
                    echo "  Items scraped: ${ITEM_COUNT}"
                fi
            else
                print_error "Failed: ${company} Grade ${grade}"
                print_warning "Check log file: ${LOG_FILE}"
                FAILED_JOBS=$((FAILED_JOBS + 1))
            fi
            
            # Random delay before next job (except for last job)
            if [[ $TOTAL_JOBS -lt $(( ${#SPIDERS[@]} * ${#GRADING_COMPANIES[@]} * ${#GRADES[@]} )) ]]; then
                DELAY=$(random_delay $MIN_DELAY $MAX_DELAY)
                print_info "Waiting ${DELAY} seconds before next job..."
                sleep "$DELAY"
            fi
        done
    done
done

################################################################################
# Summary
################################################################################

print_info "=========================================="
print_info "Scraping Job Complete"
print_info "Finished at: $(date)"
print_info "=========================================="
echo ""
echo "Summary:"
echo "  Total Jobs: ${TOTAL_JOBS}"
print_success "  Successful: ${SUCCESSFUL_JOBS}"
if [[ $FAILED_JOBS -gt 0 ]]; then
    print_error "  Failed: ${FAILED_JOBS}"
else
    echo "  Failed: ${FAILED_JOBS}"
fi
echo ""
echo "Output files saved to: ${OUTPUT_DIR}/"
echo "Log files saved to: ${LOG_DIR}/"
echo "Images saved to: ${IMAGE_DIR}/"
echo ""

# Exit with appropriate code
if [[ $FAILED_JOBS -gt 0 ]]; then
    exit 1
else
    exit 0
fi
