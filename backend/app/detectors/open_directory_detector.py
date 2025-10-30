"""
Open Directory Detector

Detects open directory listings that expose internal file structures
"""

import aiohttp
import logging
from typing import Dict
import re

logger = logging.getLogger(__name__)


class OpenDirectoryDetector:
    """Detects open directory listings"""
    
    # Common directory listing patterns
    DIRECTORY_PATTERNS = [
        r'<title>Index of /',
        r'<h1>Index of /',
        r'Directory listing for /',
        r'<title>Directory Listing',
        r'Parent Directory',
        r'\.\./',  # Parent directory link
        r'<a href="[^"]+">\.\./<',  # Apache-style parent dir
    ]
    
    # Paths commonly checked for directory listing
    COMMON_PATHS = [
        '/',
        '/uploads/',
        '/images/',
        '/files/',
        '/assets/',
        '/backup/',
        '/admin/',
        '/api/',
        '/public/',
        '/static/',
        '/media/',
        '/downloads/',
        '/docs/',
        '/data/',
    ]
    
    @staticmethod
    async def detect(url: str, timeout: int = 10) -> Dict:
        """
        Detect open directory listings
        
        Args:
            url: Base URL to check
            timeout: Request timeout
            
        Returns:
            Dictionary with directory findings
        """
        findings = {
            'has_issues': False,
            'open_directories': [],
            'severity': 'low'
        }
        
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            base_url = url.rstrip('/')
            
            async with aiohttp.ClientSession() as session:
                # Check common paths
                for path in OpenDirectoryDetector.COMMON_PATHS:
                    full_url = f'{base_url}{path}'
                    
                    try:
                        async with session.get(
                            full_url,
                            timeout=aiohttp.ClientTimeout(total=timeout),
                            allow_redirects=True,
                            ssl=False
                        ) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Check if response matches directory listing patterns
                                is_directory = OpenDirectoryDetector._is_directory_listing(content)
                                
                                if is_directory:
                                    # Extract visible files
                                    files = OpenDirectoryDetector._extract_files(content)
                                    
                                    # Assess severity based on path and files
                                    severity = OpenDirectoryDetector._assess_severity(path, files)
                                    
                                    findings['open_directories'].append({
                                        'url': full_url,
                                        'path': path,
                                        'severity': severity,
                                        'files_count': len(files),
                                        'sensitive_files': [f for f in files if OpenDirectoryDetector._is_sensitive_file(f)],
                                        'description': f'Open directory listing at {path}',
                                        'remediation': 'Disable directory listing or add index file'
                                    })
                                    
                                    findings['has_issues'] = True
                                    
                                    # Update overall severity
                                    if severity == 'critical' or findings['severity'] != 'critical':
                                        if severity == 'critical':
                                            findings['severity'] = 'critical'
                                        elif severity == 'high' and findings['severity'] not in ['critical']:
                                            findings['severity'] = 'high'
                                        elif severity == 'medium' and findings['severity'] == 'low':
                                            findings['severity'] = 'medium'
                    
                    except aiohttp.ClientError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error checking directory {full_url}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error detecting open directories for {url}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _is_directory_listing(content: str) -> bool:
        """Check if content is a directory listing"""
        for pattern in OpenDirectoryDetector.DIRECTORY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _extract_files(content: str) -> list:
        """Extract file names from directory listing"""
        files = []
        
        # Look for links in HTML
        link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, content, re.IGNORECASE)
        
        for href, text in matches:
            # Skip parent directory and current directory
            if href in ['./', '../', '..']:
                continue
            
            # Extract filename
            filename = href.split('/')[-1]
            if filename and not filename.startswith('?'):
                files.append(filename)
        
        return files[:50]  # Limit to first 50 files
    
    @staticmethod
    def _is_sensitive_file(filename: str) -> bool:
        """Check if filename indicates sensitive content"""
        sensitive_extensions = [
            '.sql', '.db', '.sqlite', '.bak', '.backup',
            '.env', '.config', '.conf', '.key', '.pem',
            '.log', '.zip', '.tar', '.gz', '.rar'
        ]
        
        sensitive_keywords = [
            'password', 'secret', 'private', 'backup',
            'config', 'database', 'admin', 'credential'
        ]
        
        filename_lower = filename.lower()
        
        # Check extensions
        for ext in sensitive_extensions:
            if filename_lower.endswith(ext):
                return True
        
        # Check keywords
        for keyword in sensitive_keywords:
            if keyword in filename_lower:
                return True
        
        return False
    
    @staticmethod
    def _assess_severity(path: str, files: list) -> str:
        """Assess severity based on path and exposed files"""
        sensitive_paths = ['/admin/', '/backup/', '/config/', '/data/', '/api/']
        
        # Check for sensitive files
        sensitive_count = sum(1 for f in files if OpenDirectoryDetector._is_sensitive_file(f))
        
        if sensitive_count > 0:
            return 'critical'
        elif any(sensitive in path.lower() for sensitive in sensitive_paths):
            return 'high'
        elif len(files) > 10:
            return 'medium'
        else:
            return 'low'

