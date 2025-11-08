#!/usr/bin/env python3
"""
Quick test to verify HXr and Mini A/P software scraping works correctly.
"""

import sys
import logging
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "macos" / "src"))

from efis_macos.grt_scraper import GRTWebScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_hxr_scraping():
    """Test HXr software scraping."""
    print("Testing HXr software scraping...")
    print("-" * 60)
    
    scraper = GRTWebScraper()
    
    # Test with the product page URL
    hxr_url = "https://grtavionics.com/product/horizon-hxr-efis/"
    
    print(f"\nScraping: {hxr_url}")
    update_info = scraper.check_hxr_software(hxr_url)
    
    if update_info:
        print("\n✅ Successfully found HXr software!")
        print(f"   Software Type: {update_info.software_type}")
        print(f"   Latest Version: {update_info.latest_version}")
        print(f"   Download URL: {update_info.download_url}")
        if update_info.file_info:
            print(f"   Description: {update_info.file_info.description}")
        return True
    else:
        print("\n❌ Failed to find HXr software")
        return False

def test_mini_ap_scraping():
    """Test Mini A/P software scraping."""
    print("\n\nTesting Mini A/P software scraping...")
    print("-" * 60)
    
    scraper = GRTWebScraper()
    
    # Test with the product page URL
    mini_ap_url = "https://grtavionics.com/product/mini-ap-efis/"
    
    print(f"\nScraping: {mini_ap_url}")
    update_info = scraper.check_mini_ap_software(mini_ap_url)
    
    if update_info:
        print("\n✅ Successfully found Mini A/P software!")
        print(f"   Software Type: {update_info.software_type}")
        print(f"   Latest Version: {update_info.latest_version}")
        print(f"   Download URL: {update_info.download_url}")
        if update_info.file_info:
            print(f"   Description: {update_info.file_info.description}")
        return True
    else:
        print("\n❌ Failed to find Mini A/P software")
        return False

if __name__ == "__main__":
    success_hxr = test_hxr_scraping()
    success_mini = test_mini_ap_scraping()
    
    print("\n" + "=" * 60)
    print(f"HXr Test: {'✅ PASSED' if success_hxr else '❌ FAILED'}")
    print(f"Mini A/P Test: {'✅ PASSED' if success_mini else '❌ FAILED'}")
    
    sys.exit(0 if (success_hxr and success_mini) else 1)
