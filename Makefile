.PHONY: help install test clean stats example

help:
	@echo "eBay Card Scraper - Available Commands"
	@echo "======================================"
	@echo "make install     - Install dependencies"
	@echo "make test        - Test the scraper setup"
	@echo "make example     - Run interactive examples"
	@echo "make stats       - Show scraping statistics"
	@echo "make clean       - Remove data and logs"
	@echo ""
	@echo "Quick Scraping Commands:"
	@echo "make psa10       - Scrape PSA 10 cards (10 results)"
	@echo "make bgs95       - Scrape BGS 9.5 cards (10 results)"
	@echo "make cgc10       - Scrape CGC 10 cards (10 results)"

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Installation complete! Run 'source venv/bin/activate' to activate."

test:
	@. venv/bin/activate && python -c "from scraper import EbayScraper; import config; print('✓ All modules loaded successfully')"
	@echo "✓ Scraper is ready to use!"

example:
	@. venv/bin/activate && python example.py

stats:
	@. venv/bin/activate && python -c "from utils import print_statistics; import config; print_statistics(config.METADATA_FILE)"

clean:
	rm -rf data/
	rm -f scraper.log
	@echo "✓ Cleaned data and logs"

# Quick scraping shortcuts
psa10:
	@. venv/bin/activate && python main.py --company PSA --grade 10 --max-results 10

bgs95:
	@. venv/bin/activate && python main.py --company BGS --grade 9.5 --max-results 10

cgc10:
	@. venv/bin/activate && python main.py --company CGC --grade 10 --max-results 10

charizard:
	@. venv/bin/activate && python main.py --company PSA --grade 10 --card-name Charizard --max-results 5
