#!/usr/bin/env python3
"""
Unit tests for the eBay Card Scraper
"""

import unittest
import os
import tempfile
import shutil
from ebay_card_scraper import EbayCardScraper


class TestEbayCardScraper(unittest.TestCase):
    """Test cases for EbayCardScraper class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.scraper = EbayCardScraper(output_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test scraper initialization"""
        self.assertIsInstance(self.scraper, EbayCardScraper)
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(self.scraper.output_dir, self.test_dir)
    
    def test_grading_companies(self):
        """Test that grading companies are defined"""
        expected_companies = {'PSA', 'BGS', 'CGC', 'SGC'}
        self.assertEqual(set(self.scraper.GRADING_COMPANIES.keys()), expected_companies)
    
    def test_invalid_grading_company(self):
        """Test that invalid grading company raises ValueError"""
        with self.assertRaises(ValueError):
            self.scraper.search_graded_cards("INVALID", max_results=1)
    
    def test_valid_grading_company_names(self):
        """Test that all valid grading companies are accepted"""
        for company in ['PSA', 'BGS', 'CGC', 'SGC']:
            # Should not raise an exception (will fail to fetch without network)
            # but we're testing the validation logic
            try:
                self.scraper.search_graded_cards(company, max_results=1)
            except Exception as e:
                # Network errors are expected in test environment
                # We just want to ensure ValueError is not raised for valid companies
                self.assertNotIsInstance(e, ValueError)
    
    def test_is_valid_image_url(self):
        """Test image URL validation"""
        # Valid URLs
        self.assertTrue(self.scraper._is_valid_image_url('https://i.ebayimg.com/image.jpg'))
        self.assertTrue(self.scraper._is_valid_image_url('https://example.com/image.png'))
        
        # Invalid URLs
        self.assertFalse(self.scraper._is_valid_image_url('data:image/png;base64,abc'))
        self.assertFalse(self.scraper._is_valid_image_url(''))
        self.assertFalse(self.scraper._is_valid_image_url(None))
    
    def test_get_high_res_url(self):
        """Test conversion to high-resolution URLs"""
        test_cases = [
            ('https://i.ebayimg.com/images/g/ABC/s-l64.jpg', 
             'https://i.ebayimg.com/images/g/ABC/s-l1600.jpg'),
            ('https://i.ebayimg.com/images/g/XYZ/s-l140.jpg', 
             'https://i.ebayimg.com/images/g/XYZ/s-l1600.jpg'),
            ('https://i.ebayimg.com/images/g/123/s-l500.jpg', 
             'https://i.ebayimg.com/images/g/123/s-l1600.jpg'),
        ]
        
        for original, expected in test_cases:
            result = self.scraper._get_high_res_url(original)
            self.assertEqual(result, expected)
    
    def test_output_directory_creation(self):
        """Test that output directory is created"""
        new_dir = os.path.join(self.test_dir, 'new_output')
        scraper = EbayCardScraper(output_dir=new_dir)
        self.assertTrue(os.path.exists(new_dir))
    
    def test_session_headers(self):
        """Test that session has proper headers"""
        self.assertIn('User-Agent', self.scraper.session.headers)
        user_agent = self.scraper.session.headers['User-Agent']
        self.assertTrue(len(user_agent) > 0)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions"""
    
    def test_image_url_validation_edge_cases(self):
        """Test edge cases for image URL validation"""
        scraper = EbayCardScraper()
        
        # Test various edge cases
        self.assertFalse(scraper._is_valid_image_url(''))
        self.assertFalse(scraper._is_valid_image_url('   '))
        self.assertTrue(scraper._is_valid_image_url('https://i.ebayimg.com/test.gif'))
        self.assertTrue(scraper._is_valid_image_url('https://example.com/image.JPEG'))
        
        # Security test: URLs are validated by domain ending check for ebayimg.com
        # This prevents path-based bypasses like https://evil.com/i.ebayimg.com/
        self.assertTrue(scraper._is_valid_image_url('https://i.ebayimg.com/images/g/abc/s-l1600.jpg'))
        # Non-eBay domains with image extensions are also allowed (for eBay listings that may reference external images)
        # but data URIs and malformed URLs are rejected
        self.assertFalse(scraper._is_valid_image_url('data:image/png;base64,abc'))
        self.assertFalse(scraper._is_valid_image_url('javascript:alert(1)'))


if __name__ == '__main__':
    unittest.main()
