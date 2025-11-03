"""
Unit tests for GRT scraper core functionality.
"""

import pytest
import tempfile
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from macos.src.efis_macos.grt_scraper import (
    GRTWebScraper, VersionInfo, UpdateInfo, 
    RateLimiter, CacheManager, ScrapingError
)


class TestVersionInfo:
    """Test cases for VersionInfo dataclass."""

    def test_create_version_info(self):
        """Test creating VersionInfo instance."""
        version = VersionInfo(
            software_type="hxr",
            version="8.01",
            download_url="http://example.com/hxr.zip",
            file_size=1024000,
            release_date=datetime.now()
        )
        
        assert version.software_type == "hxr"
        assert version.version == "8.01"
        assert version.download_url == "http://example.com/hxr.zip"
        assert version.file_size == 1024000

    def test_version_info_equality(self):
        """Test VersionInfo equality comparison."""
        now = datetime.now()
        version1 = VersionInfo("hxr", "8.01", "http://example.com", 1024, now)
        version2 = VersionInfo("hxr", "8.01", "http://example.com", 1024, now)
        
        assert version1 == version2

    def test_version_info_inequality(self):
        """Test VersionInfo inequality comparison."""
        now = datetime.now()
        version1 = VersionInfo("hxr", "8.01", "http://example.com", 1024, now)
        version2 = VersionInfo("hxr", "8.02", "http://example.com", 1024, now)
        
        assert version1 != version2


class TestRateLimiter:
    """Test cases for RateLimiter."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(min_interval=1.0)
        assert limiter.min_interval == 1.0
        assert limiter.last_request_time is None

    def test_rate_limiter_first_request(self):
        """Test first request doesn't wait."""
        limiter = RateLimiter(min_interval=0.1)
        
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # First request should not wait
        assert elapsed < 0.05

    def test_rate_limiter_subsequent_requests(self):
        """Test subsequent requests respect rate limit."""
        limiter = RateLimiter(min_interval=0.1)
        
        # First request
        limiter.wait_if_needed()
        
        # Second request should wait
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        assert elapsed >= 0.09  # Allow small timing variance

    def test_rate_limiter_no_wait_after_interval(self):
        """Test no wait if enough time has passed."""
        limiter = RateLimiter(min_interval=0.1)
        
        # First request
        limiter.wait_if_needed()
        
        # Wait longer than interval
        time.sleep(0.15)
        
        # Second request should not wait
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        assert elapsed < 0.05


class TestCacheManager:
    """Test cases for CacheManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(self.temp_dir, cache_duration=3600)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_response(self):
        """Test caching HTTP response."""
        url = "http://example.com/test"
        data = {"content": "test data", "timestamp": "2023-12-01"}
        
        self.cache_manager.cache_response(url, data)
        
        # Verify cache file was created
        cache_files = list(Path(self.temp_dir).glob("*.json"))
        assert len(cache_files) == 1

    def test_get_cached_response_valid(self):
        """Test getting valid cached response."""
        url = "http://example.com/test"
        data = {"content": "test data"}
        
        self.cache_manager.cache_response(url, data)
        cached_data = self.cache_manager.get_cached_response(url)
        
        assert cached_data == data

    def test_get_cached_response_expired(self):
        """Test getting expired cached response."""
        # Create cache manager with very short duration
        short_cache = CacheManager(self.temp_dir, cache_duration=0.1)
        
        url = "http://example.com/test"
        data = {"content": "test data"}
        
        short_cache.cache_response(url, data)
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        cached_data = short_cache.get_cached_response(url)
        assert cached_data is None

    def test_get_cached_response_not_found(self):
        """Test getting non-existent cached response."""
        cached_data = self.cache_manager.get_cached_response("http://nonexistent.com")
        assert cached_data is None

    def test_clear_expired_cache(self):
        """Test clearing expired cache entries."""
        # Create cache manager with short duration
        short_cache = CacheManager(self.temp_dir, cache_duration=0.1)
        
        # Cache multiple responses
        urls = ["http://example.com/1", "http://example.com/2"]
        for url in urls:
            short_cache.cache_response(url, {"data": url})
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Clear expired entries
        short_cache.clear_expired_cache()
        
        # Verify cache files were removed
        cache_files = list(Path(self.temp_dir).glob("*.json"))
        assert len(cache_files) == 0

    def test_get_cache_filename(self):
        """Test cache filename generation."""
        url = "http://example.com/test?param=value"
        filename = self.cache_manager._get_cache_filename(url)
        
        assert filename.endswith(".json")
        assert "/" not in filename
        assert "?" not in filename


class TestGRTWebScraper:
    """Test cases for GRTWebScraper core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'macos': {
                'grtUrls': {
                    'navDatabase': 'http://example.com/nav',
                    'hxrSoftware': 'http://example.com/hxr',
                    'miniAPSoftware': 'http://example.com/mini',
                    'ahrsSoftware': 'http://example.com/ahrs',
                    'servoSoftware': 'http://example.com/servo'
                }
            }
        }
        self.scraper = GRTWebScraper(self.config, cache_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_version_from_url(self):
        """Test version extraction from URL paths."""
        test_cases = [
            ("/HXr/8/01/", "hxr", "8.01"),
            ("/HXr/7/15/", "hxr", "7.15"),
            ("/Mini/2/05/", "mini_ap", "2.05"),
            ("/AHRS/1/23/", "ahrs", "1.23")
        ]
        
        for url_path, software_type, expected_version in test_cases:
            result = self.scraper._extract_version_from_url(url_path, software_type)
            assert result == expected_version

    def test_extract_version_from_text(self):
        """Test version extraction from text content."""
        test_cases = [
            ("Version 2.5 Release", "mini_ap", "2.5"),
            ("v3.14 Software Update", "hxr", "3.14"),
            ("Mini A/P Version 1.8", "mini_ap", "1.8"),
            ("AHRS v2.0.1", "ahrs", "2.0.1")
        ]
        
        for text, software_type, expected_version in test_cases:
            result = self.scraper._extract_version_from_text(text, software_type)
            assert result == expected_version

    def test_extract_version_no_match(self):
        """Test version extraction with no matches."""
        result = self.scraper._extract_version_from_text("No version here", "hxr")
        assert result is None
        
        result = self.scraper._extract_version_from_url("/invalid/path/", "hxr")
        assert result is None

    def test_parse_file_size(self):
        """Test file size parsing from text."""
        test_cases = [
            ("File size: 1.5 MB", 1572864),  # 1.5 * 1024 * 1024
            ("Download (2.3MB)", 2411724),   # 2.3 * 1024 * 1024
            ("Size: 512 KB", 524288),        # 512 * 1024
            ("1024 bytes", 1024),
            ("No size info", None)
        ]
        
        for text, expected_size in test_cases:
            result = self.scraper._parse_file_size(text)
            if expected_size is None:
                assert result is None
            else:
                assert abs(result - expected_size) < 1000  # Allow small variance

    def test_validate_download_url(self):
        """Test download URL validation."""
        valid_urls = [
            "https://grtavionics.com/download/file.zip",
            "http://grtavionics.com/software/update.bin",
            "https://www.grtavionics.com/files/nav.db"
        ]
        
        invalid_urls = [
            "ftp://example.com/file.zip",
            "javascript:alert('xss')",
            "http://malicious.com/file.exe",
            "not_a_url",
            ""
        ]
        
        for url in valid_urls:
            assert self.scraper._validate_download_url(url) is True
        
        for url in invalid_urls:
            assert self.scraper._validate_download_url(url) is False

    def test_compare_versions(self):
        """Test version comparison logic."""
        test_cases = [
            ("1.0", "2.0", -1),    # 1.0 < 2.0
            ("2.0", "1.0", 1),     # 2.0 > 1.0
            ("1.5", "1.5", 0),     # 1.5 == 1.5
            ("1.10", "1.2", 1),    # 1.10 > 1.2
            ("2.0.1", "2.0", 1),   # 2.0.1 > 2.0
            ("1.0.0", "1.0", 0),   # 1.0.0 == 1.0
        ]
        
        for v1, v2, expected in test_cases:
            result = self.scraper._compare_versions(v1, v2)
            assert result == expected

    @patch('macos.src.efis_macos.grt_scraper.requests.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        content = self.scraper._fetch_page("http://example.com")
        
        assert content == "<html><body>Test content</body></html>"
        mock_get.assert_called_once()

    @patch('macos.src.efis_macos.grt_scraper.requests.get')
    def test_fetch_page_http_error(self, mock_get):
        """Test page fetching with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(ScrapingError) as exc_info:
            self.scraper._fetch_page("http://example.com/notfound")
        
        assert "Failed to fetch page" in str(exc_info.value)

    @patch('macos.src.efis_macos.grt_scraper.requests.get')
    def test_fetch_page_with_cache(self, mock_get):
        """Test page fetching with caching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Cached content</html>"
        mock_get.return_value = mock_response
        
        url = "http://example.com/cached"
        
        # First request should hit the network
        content1 = self.scraper._fetch_page(url)
        assert mock_get.call_count == 1
        
        # Second request should use cache
        content2 = self.scraper._fetch_page(url)
        assert mock_get.call_count == 1  # No additional network call
        assert content1 == content2

    def test_create_update_info(self):
        """Test creating UpdateInfo from VersionInfo."""
        version_info = VersionInfo(
            software_type="hxr",
            version="8.01",
            download_url="http://example.com/hxr.zip",
            file_size=1024000,
            release_date=datetime.now()
        )
        
        update_info = self.scraper._create_update_info(version_info, "7.15")
        
        assert update_info.software_type == "hxr"
        assert update_info.current_version == "7.15"
        assert update_info.new_version == "8.01"
        assert update_info.download_url == "http://example.com/hxr.zip"
        assert update_info.needs_update is True

    def test_create_update_info_no_update_needed(self):
        """Test creating UpdateInfo when no update is needed."""
        version_info = VersionInfo(
            software_type="hxr",
            version="8.01",
            download_url="http://example.com/hxr.zip",
            file_size=1024000,
            release_date=datetime.now()
        )
        
        update_info = self.scraper._create_update_info(version_info, "8.01")
        
        assert update_info.needs_update is False
        assert update_info.current_version == "8.01"
        assert update_info.new_version == "8.01"