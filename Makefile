.PHONY: help install test clean stats example

help:
	@echo "Graded Pokemon Card Scraper - Available Commands"
	@echo "================================================"
	@echo "make install     - Install dependencies"
	@echo "make test        - Test the scraper setup"
	@echo "make example     - Run interactive examples"
	@echo "make clean       - Remove data and logs"
	@echo ""
	@echo "Quick Scraping Commands (eBay):"
	@echo "make ebay-psa10  - Scrape PSA 10 from eBay (10 results)"
	@echo "make ebay-bgs95  - Scrape BGS 9.5 from eBay (10 results)"
	@echo "make ebay-cgc10  - Scrape CGC 10 from eBay (10 results)"
	@echo ""
	@echo "Quick Scraping Commands (Mercari):"
	@echo "make mercari-psa10 - Scrape PSA 10 from Mercari (10 results)"
	@echo "make mercari-bgs95 - Scrape BGS 9.5 from Mercari (10 results)"
	@echo ""
	@echo "Multi-Marketplace:"
	@echo "make both-psa10  - Scrape PSA 10 from both (10 results each)"

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Installation complete! Run 'source venv/bin/activate' to activate."

test:
	@. venv/bin/activate && python -c "from scrapers import EbayScraper, MercariScraper; import config; print('✓ All modules loaded successfully')"
	@echo "✓ Scraper is ready to use!"

example:
	@. venv/bin/activate && python examples.py

clean:
	rm -rf data/
	rm -f scraper.log
	rm -f ebay_debug.html mercari_debug.html
	@echo "✓ Cleaned data and logs"

# eBay scraping shortcuts
ebay-psa10:
	@. venv/bin/activate && python main.py --marketplace ebay --company PSA --grade 10 --max-results 10

ebay-bgs95:
	@. venv/bin/activate && python main.py --marketplace ebay --company BGS --grade 9.5 --max-results 10

ebay-cgc10:
	@. venv/bin/activate && python main.py --marketplace ebay --company CGC --grade 10 --max-results 10

# Mercari scraping shortcuts
mercari-psa10:
	@. venv/bin/activate && python main.py --marketplace mercari --company PSA --grade 10 --max-results 10

mercari-bgs95:
	@. venv/bin/activate && python main.py --marketplace mercari --company BGS --grade 9.5 --max-results 10

# Multi-marketplace shortcuts
both-psa10:
	@. venv/bin/activate && python main.py --marketplace both --company PSA --grade 10 --max-results 10

charizard:
	@. venv/bin/activate && python main.py --marketplace ebay --company PSA --grade 10 --card-name Charizard --max-results 5
