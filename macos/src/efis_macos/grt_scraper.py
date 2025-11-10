"""
GRT Avionics website scraping module for software and database updates.
"""

import re
import time
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import json

try:
    import requests
    from bs4 import BeautifulSoup
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    # Create mock classes for when dependencies aren't available
    requests = None
    BeautifulSoup = None
    DEPENDENCIES_AVAILABLE = False


@dataclass
class VersionInfo:
    """Information about a software version."""
    name: str
    version: str
    url: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    last_modified: Optional[datetime] = None
    description: Optional[str] = None


@dataclass
class UpdateInfo:
    """Information about available updates."""
    software_type: str
    current_version: Optional[str]
    latest_version: str
    download_url: str
    needs_update: bool
    file_info: Optional[VersionInfo] = None


class RateLimiter:
    """Simple rate limiter to avoid overwhelming the server."""
    
    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self.last_request = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limiting."""
        now = time.time()
        elapsed = now - self.last_request
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request = time.time()


class CacheManager:
    """Manages caching of web requests to minimize server load."""
    
    def __init__(self, cache_dir: str, cache_duration: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration  # seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"cache_{url_hash}.json"
    
    def get_cached_response(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached response if it exists and is not expired."""
        cache_path = self._get_cache_path(url)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(seconds=self.cache_duration):
                cache_path.unlink()  # Remove expired cache
                return None
            
            self.logger.debug(f"Using cached response for {url}")
            return cache_data['response']
            
        except Exception as e:
            self.logger.warning(f"Error reading cache for {url}: {e}")
            return None
    
    def cache_response(self, url: str, response_data: Dict[str, Any]):
        """Cache a response."""
        cache_path = self._get_cache_path(url)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'response': response_data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.logger.debug(f"Cached response for {url}")
            
        except Exception as e:
            self.logger.warning(f"Error caching response for {url}: {e}")


class GRTWebScraper:
    """Scrapes GRT Avionics website for software updates."""
    
    def __init__(self, cache_dir: str = "/tmp/grt_cache", rate_limit: float = 2.0):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies (requests, beautifulsoup4) not available")
        
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(rate_limit)
        self.cache_manager = CacheManager(cache_dir)
        
        # HTTP session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Version patterns for different software types
        self.version_patterns = {
            'hxr': [
                r'/HXr/(\d+)/(\d+)/',  # URL path pattern like /HXr/8/01/
                r'Version\s+(\d+\.\d+)',  # Version X.Y in text
                r'v(\d+\.\d+)',  # vX.Y format
            ],
            'mini_ap': [
                r'/Mini(?:AP)?/(\d+)/(\d+)/',  # URL path pattern like /MiniAP/7/05/
                r'Version\s+(\d+\.\d+)',
                r'v(\d+\.\d+)',
                r'Mini.*?(\d+\.\d+)',
            ],
            'ahrs': [
                r'MiniAHRSUp(\d)(\d)',  # Filename pattern like MiniAHRSUp71.dat -> 7.1
                r'AHRS.*?(\d+\.\d+)',
                r'Version\s+(\d+\.\d+)',
                r'v(\d+\.\d+)',
            ],
            'servo': [
                r'ServoUp(\d)(\d)',  # Filename pattern like ServoUp14.dat -> 1.4
                r'Servo.*?(\d+\.\d+)',
                r'Version\s+(\d+\.\d+)',
                r'v(\d+\.\d+)',
            ]
        }
    
    def _make_request(self, url: str) -> Optional[Any]:
        """Make HTTP request with rate limiting and error handling."""
        # Check cache first
        cached_response = self.cache_manager.get_cached_response(url)
        if cached_response:
            # Create a mock response object for cached data
            response = requests.Response()
            response._content = cached_response['content'].encode()
            response.status_code = cached_response['status_code']
            response.headers.update(cached_response['headers'])
            return response
        
        # Rate limit
        self.rate_limiter.wait_if_needed()
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the response
            cache_data = {
                'content': response.text,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            self.cache_manager.cache_response(url, cache_data)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _parse_html(self, html_content: str) -> Any:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html_content, 'html.parser')
    
    def _extract_version_from_url(self, url: str, software_type: str) -> Optional[str]:
        """Extract version information from URL path."""
        patterns = self.version_patterns.get(software_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 2:  # For patterns like /HXr/8/01/
                    return f"{match.group(1)}.{match.group(2)}"
                else:
                    return match.group(1)
        
        return None
    
    def _extract_version_from_text(self, text: str, software_type: str) -> Optional[str]:
        """Extract version information from text content."""
        patterns = self.version_patterns.get(software_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _find_download_links(self, soup: Any, base_url: str) -> List[Tuple[str, str]]:
        """Find download links on the page."""
        links = []
        
        # Look for common download file extensions
        download_extensions = ['.zip', '.exe', '.dmg', '.pkg', '.tar.gz', '.db']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Check if it's a download link
            if any(href.lower().endswith(ext) for ext in download_extensions):
                link_text = link.get_text(strip=True)
                links.append((href, link_text))
        
        return links
    
    def check_nav_database(self, nav_url: str) -> Optional[UpdateInfo]:
        """Check for NAV database updates."""
        self.logger.info("Checking NAV database updates...")
        
        response = self._make_request(nav_url)
        if not response:
            return None
        
        soup = self._parse_html(response.text)
        download_links = self._find_download_links(soup, nav_url)
        
        # Look for NAV.DB or similar files
        nav_links = [link for link in download_links 
                    if 'nav' in link[1].lower() or link[0].lower().endswith('.db')]
        
        if not nav_links:
            self.logger.warning("No NAV database download links found")
            return None
        
        # Use the first NAV database link found
        download_url, link_text = nav_links[0]
        
        # Try to extract version/date information
        version = self._extract_version_from_text(link_text, 'nav')
        if not version:
            # Use current date as version if no version found
            version = datetime.now().strftime("%Y-%m-%d")
        
        return UpdateInfo(
            software_type="nav_database",
            current_version=None,  # Will be determined by comparing with local file
            latest_version=version,
            download_url=download_url,
            needs_update=True,  # Will be determined by file comparison
            file_info=VersionInfo(
                name="NAV Database",
                version=version,
                url=download_url,
                description=link_text
            )
        )
    
    def check_hxr_software(self, hxr_url: str) -> Optional[UpdateInfo]:
        """Check for HXr software updates."""
        self.logger.info("Checking HXr software updates...")
        
        response = self._make_request(hxr_url)
        if not response:
            return None
        
        soup = self._parse_html(response.text)
        
        # Look for links that match the HXr software pattern
        # Pattern: https://grtavionics.com/getfile.aspx/HXr/X/YY/HHXRUp.dat
        download_url = None
        version = None
        
        # Search for all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if this is an HXr software download link
            if 'getfile.aspx' in href and 'HXr' in href and 'HHXRUp.dat' in href:
                # Convert relative URL to absolute
                if not href.startswith('http'):
                    href = urljoin(hxr_url, href)
                
                download_url = href
                
                # Extract version from URL path: /HXr/8/01/ -> 8.01
                version_match = re.search(r'/HXr/(\d+)/(\d+)/', href)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
                
                self.logger.info(f"Found HXr software: version {version}, URL: {download_url}")
                break
        
        # If no direct download link found, try to find any HXr-related links
        if not download_url:
            download_links = self._find_download_links(soup, hxr_url)
            hxr_links = [link for link in download_links 
                        if 'hxr' in link[1].lower() or 'hxr' in link[0].lower()]
            
            if hxr_links:
                download_url, link_text = hxr_links[0]
                # Try to extract version from the URL
                version = self._extract_version_from_url(download_url, 'hxr')
        
        # If still no version, try to extract from page content
        if not version:
            page_text = soup.get_text()
            version = self._extract_version_from_text(page_text, 'hxr')
        
        if not download_url:
            self.logger.warning("No HXr software download links found")
            return None
        
        return UpdateInfo(
            software_type="hxr_software",
            current_version=None,
            latest_version=version or "unknown",
            download_url=download_url,
            needs_update=True,
            file_info=VersionInfo(
                name="HXr Software",
                version=version or "unknown",
                url=download_url,
                description=f"HXr EFIS Software v{version}" if version else "HXr EFIS Software"
            )
        )
    
    def check_mini_ap_software(self, mini_ap_url: str) -> Optional[UpdateInfo]:
        """Check for Mini A/P software updates."""
        self.logger.info("Checking Mini A/P software updates...")
        
        response = self._make_request(mini_ap_url)
        if not response:
            return None
        
        soup = self._parse_html(response.text)
        
        # Look for "Display Unit Software" link on the product page
        download_url = None
        version = None
        
        # Search for all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # Look for "Display Unit Software" link
            if 'display unit software' in link_text.lower():
                # Convert relative URL to absolute
                if not href.startswith('http'):
                    href = urljoin(mini_ap_url, href)
                
                download_url = href
                
                # Try to extract version from URL path
                # Pattern similar to HXr: /MiniAP/X/YY/ or /Mini/X/YY/
                version_match = re.search(r'/Mini(?:AP)?/(\d+)/(\d+)/', href)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
                
                self.logger.info(f"Found Mini A/P software: version {version}, URL: {download_url}")
                break
        
        # If no "Display Unit Software" link found, try generic approach
        if not download_url:
            # Look for getfile.aspx links with Mini or MiniAP in them
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if 'getfile.aspx' in href and ('Mini' in href or 'mini' in href):
                    if not href.startswith('http'):
                        href = urljoin(mini_ap_url, href)
                    
                    download_url = href
                    version_match = re.search(r'/Mini(?:AP)?/(\d+)/(\d+)/', href)
                    if version_match:
                        major = version_match.group(1)
                        minor = version_match.group(2)
                        version = f"{major}.{minor}"
                    break
        
        # If still no download link, try old approach
        if not download_url:
            download_links = self._find_download_links(soup, mini_ap_url)
            mini_ap_links = [link for link in download_links 
                            if 'mini' in link[1].lower() or 'ap' in link[1].lower()]
            
            if mini_ap_links:
                download_url, link_text = mini_ap_links[0]
                version = self._extract_version_from_url(download_url, 'mini_ap')
        
        # If still no version, try to extract from page content
        if not version:
            page_text = soup.get_text()
            version = self._extract_version_from_text(page_text, 'mini_ap')
        
        if not download_url:
            self.logger.warning("No Mini A/P software download links found")
            return None
        
        return UpdateInfo(
            software_type="mini_ap_software",
            current_version=None,
            latest_version=version or "unknown",
            download_url=download_url,
            needs_update=True,
            file_info=VersionInfo(
                name="Mini A/P Software",
                version=version or "unknown",
                url=download_url,
                description=f"Mini A/P Display Unit Software v{version}" if version else "Mini A/P Display Unit Software"
            )
        )
    
    def check_ahrs_software(self, ahrs_url: str) -> Optional[UpdateInfo]:
        """Check for AHRS software updates (Mini AHRS)."""
        self.logger.info("Checking AHRS software updates...")
        
        response = self._make_request(ahrs_url)
        if not response:
            return None
        
        soup = self._parse_html(response.text)
        
        # Look for AHRS software link on the product page
        # Pattern: https://grtavionics.com/getfile.aspx/Mini/AHRS/MiniAHRSUpXY.dat
        download_url = None
        version = None
        
        # Search for all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # Look for AHRS-related links
            if 'ahrs' in link_text.lower() or 'MiniAHRS' in href:
                # Convert relative URL to absolute
                if not href.startswith('http'):
                    href = urljoin(ahrs_url, href)
                
                download_url = href
                
                # Extract version from filename: MiniAHRSUp71.dat -> 7.1
                version_match = re.search(r'MiniAHRSUp(\d)(\d)', href)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
                
                self.logger.info(f"Found AHRS software: version {version}, URL: {download_url}")
                break
        
        # If no direct link found, try generic approach
        if not download_url:
            download_links = self._find_download_links(soup, ahrs_url)
            ahrs_links = [link for link in download_links 
                         if 'ahrs' in link[1].lower() or 'ahrs' in link[0].lower()]
            
            if ahrs_links:
                download_url, link_text = ahrs_links[0]
                # Try to extract version from filename
                version_match = re.search(r'MiniAHRSUp(\d)(\d)', download_url)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
        
        # If still no version, try to extract from page content
        if not version:
            page_text = soup.get_text()
            version = self._extract_version_from_text(page_text, 'ahrs')
        
        if not download_url:
            self.logger.warning("No AHRS software download links found")
            return None
        
        return UpdateInfo(
            software_type="ahrs_software",
            current_version=None,
            latest_version=version or "unknown",
            download_url=download_url,
            needs_update=True,
            file_info=VersionInfo(
                name="AHRS Software",
                version=version or "unknown",
                url=download_url,
                description=link_text
            )
        )
    
    def check_servo_software(self, servo_url: str) -> Optional[UpdateInfo]:
        """Check for Servo software updates."""
        self.logger.info("Checking Servo software updates...")
        
        # If the URL is a direct download link, extract version from it
        if 'getfile.aspx' in servo_url and 'ServoUp' in servo_url:
            download_url = servo_url
            version = None
            
            # Extract version from filename: ServoUp14.dat -> 1.4
            version_match = re.search(r'ServoUp(\d)(\d)', servo_url)
            if version_match:
                major = version_match.group(1)
                minor = version_match.group(2)
                version = f"{major}.{minor}"
            
            self.logger.info(f"Found Servo software: version {version}, URL: {download_url}")
            
            return UpdateInfo(
                software_type="servo_software",
                current_version=None,
                latest_version=version or "unknown",
                download_url=download_url,
                needs_update=True,
                file_info=VersionInfo(
                    name="Servo Software",
                    version=version or "unknown",
                    url=download_url,
                    description=f"Autopilot Servo Software v{version}" if version else "Autopilot Servo Software"
                )
            )
        
        # Otherwise, scrape the page for links
        response = self._make_request(servo_url)
        if not response:
            return None
        
        soup = self._parse_html(response.text)
        
        # Look for servo software links
        download_url = None
        version = None
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if 'ServoUp' in href or ('servo' in href.lower() and 'getfile.aspx' in href):
                if not href.startswith('http'):
                    href = urljoin(servo_url, href)
                
                download_url = href
                
                # Extract version from filename
                version_match = re.search(r'ServoUp(\d)(\d)', href)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
                
                self.logger.info(f"Found Servo software: version {version}, URL: {download_url}")
                break
        
        # Fallback to generic approach
        if not download_url:
            download_links = self._find_download_links(soup, servo_url)
            servo_links = [link for link in download_links 
                          if 'servo' in link[1].lower()]
            
            if servo_links:
                download_url, link_text = servo_links[0]
                version_match = re.search(r'ServoUp(\d)(\d)', download_url)
                if version_match:
                    major = version_match.group(1)
                    minor = version_match.group(2)
                    version = f"{major}.{minor}"
        
        # If still no version, try page content
        if not version:
            page_text = soup.get_text()
            version = self._extract_version_from_text(page_text, 'servo')
        
        if not download_url:
            self.logger.warning("No Servo software download links found")
            return None
        
        return UpdateInfo(
            software_type="servo_software",
            current_version=None,
            latest_version=version or "unknown",
            download_url=download_url,
            needs_update=True,
            file_info=VersionInfo(
                name="Servo Software",
                version=version or "unknown",
                url=download_url,
                description=link_text
            )
        )
    
    def check_for_updates(self, grt_urls: Dict[str, str]) -> List[UpdateInfo]:
        """Check all GRT software for updates."""
        self.logger.info("Starting GRT software update check...")
        
        updates = []
        
        # Check each software type
        checkers = {
            'nav_database': self.check_nav_database,
            'hxr_software': self.check_hxr_software,
            'mini_ap_software': self.check_mini_ap_software,
            'ahrs_software': self.check_ahrs_software,
            'servo_software': self.check_servo_software,
        }
        
        for software_type, url in grt_urls.items():
            if software_type in checkers:
                try:
                    update_info = checkers[software_type](url)
                    if update_info:
                        updates.append(update_info)
                except Exception as e:
                    self.logger.error(f"Error checking {software_type}: {e}")
        
        self.logger.info(f"Found {len(updates)} potential updates")
        return updates