"""
Base scraper class for all marketplace scrapers.
"""

import os
import time
import random
import requests
import logging
from PIL import Image
from io import BytesIO
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import re
from abc import ABC, abstractmethod

import config


class BaseScraper(ABC):
    """Base class for marketplace scrapers"""
    
    def __init__(self, marketplace_name: str, output_dir: str = None):
        """
        Initialize base scraper.
        
        Args:
            marketplace_name: Name of marketplace (e.g., 'ebay', 'mercari')
            output_dir: Directory to save images and metadata
        """
        self.marketplace = marketplace_name
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.images_dir = os.path.join(self.output_dir, 'images', marketplace_name)
        self.metadata_file = os.path.join(self.output_dir, f'{marketplace_name}_metadata.csv')
        
        # Create output directories
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{marketplace_name}_scraper")
        
        # Initialize metadata storage
        self.metadata = []
        self._load_existing_metadata()
    
    def _load_existing_metadata(self):
        """Load existing metadata if available"""
        if os.path.exists(self.metadata_file):
            try:
                existing_df = pd.read_csv(self.metadata_file)
                self.metadata = existing_df.to_dict('records')
                self.logger.info(f"Loaded {len(self.metadata)} existing records")
            except Exception as e:
                self.logger.warning(f"Could not load existing metadata: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get random user agent headers for requests"""
        return {
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        Download and save an image from URL.
        
        Args:
            image_url: URL of the image
            filename: Filename to save the image as
            
        Returns:
            Path to saved image or None if download fails
        """
        try:
            response = requests.get(image_url, headers=self._get_headers(), 
                                   timeout=config.TIMEOUT)
            response.raise_for_status()
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > config.MAX_IMAGE_SIZE[0] or img.size[1] > config.MAX_IMAGE_SIZE[1]:
                img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save image
            filepath = os.path.join(self.images_dir, filename)
            img.save(filepath, config.IMAGE_FORMAT, quality=config.IMAGE_QUALITY)
            
            self.logger.info(f"Saved image: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error downloading image from {image_url}: {e}")
            return None
    
    def _sanitize_filename(self, text: str) -> str:
        """Remove invalid characters from filename"""
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')[:50]
    
    def _save_metadata(self):
        """Save metadata to CSV file"""
        try:
            df = pd.DataFrame(self.metadata)
            df.to_csv(self.metadata_file, index=False)
            self.logger.info(f"Saved metadata to {self.metadata_file}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
    
    @abstractmethod
    def search_graded_cards(self, grading_company: str, grade: float, 
                           card_name: str = None, max_results: int = 50,
                           **kwargs) -> int:
        """
        Search for graded cards. Must be implemented by subclasses.
        
        Args:
            grading_company: PSA, BGS, or CGC
            grade: Card grade
            card_name: Optional card name
            max_results: Maximum results to scrape
            
        Returns:
            Number of images downloaded
        """
        pass
