"""
Web Header Analyzer

Checks for missing or misconfigured HTTP security headers
"""

import aiohttp
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class WebHeaderAnalyzer:
    """Analyzes HTTP security headers for vulnerabilities"""
    
    REQUIRED_HEADERS = {
        'Content-Security-Policy': 'critical',
        'Strict-Transport-Security': 'critical',
        'X-Frame-Options': 'high',
        'X-Content-Type-Options': 'high',
        'X-XSS-Protection': 'medium',
        'Referrer-Policy': 'medium',
        'Permissions-Policy': 'low',
    }
    
    @staticmethod
    async def analyze(url: str, timeout: int = 10) -> Dict:
        """
        Analyze HTTP security headers for a given URL
        
        Args:
            url: Target URL to analyze
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with findings
        """
        findings = {
            'has_issues': False,
            'missing_headers': [],
            'weak_headers': [],
            'good_headers': [],
            'severity': 'low',
            'score': 0
        }
        
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    ssl=False
                ) as response:
                    headers = response.headers
                    
                    # Check each required header
                    for header, severity in WebHeaderAnalyzer.REQUIRED_HEADERS.items():
                        if header not in headers:
                            findings['missing_headers'].append({
                                'header': header,
                                'severity': severity,
                                'description': WebHeaderAnalyzer._get_header_description(header)
                            })
                            findings['has_issues'] = True
                        else:
                            # Check if header value is weak
                            value = headers[header]
                            if WebHeaderAnalyzer._is_weak_header(header, value):
                                findings['weak_headers'].append({
                                    'header': header,
                                    'value': value,
                                    'severity': severity,
                                    'issue': WebHeaderAnalyzer._get_weakness_reason(header, value)
                                })
                                findings['has_issues'] = True
                            else:
                                findings['good_headers'].append(header)
                    
                    # Calculate severity
                    if any(h['severity'] == 'critical' for h in findings['missing_headers']):
                        findings['severity'] = 'critical'
                    elif any(h['severity'] == 'high' for h in findings['missing_headers']):
                        findings['severity'] = 'high'
                    elif findings['missing_headers']:
                        findings['severity'] = 'medium'
                    
                    # Calculate score (0-100, lower is worse)
                    total_headers = len(WebHeaderAnalyzer.REQUIRED_HEADERS)
                    good_count = len(findings['good_headers'])
                    findings['score'] = int((good_count / total_headers) * 100)
                    
        except aiohttp.ClientError as e:
            logger.warning(f"Failed to analyze headers for {url}: {str(e)}")
            findings['error'] = str(e)
        except asyncio.TimeoutError as e:
            logger.warning(f"Timeout analyzing headers for {url}")
            findings['error'] = 'Timeout'
        except Exception as e:
            logger.error(f"Unexpected error analyzing headers for {url}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _is_weak_header(header: str, value: str) -> bool:
        """Check if header value is weak or misconfigured"""
        value_lower = value.lower()
        
        if header == 'X-Frame-Options':
            return value_lower not in ['deny', 'sameorigin']
        elif header == 'X-Content-Type-Options':
            return value_lower != 'nosniff'
        elif header == 'Strict-Transport-Security':
            # Should have max-age and ideally includeSubDomains
            return 'max-age' not in value_lower or int(value.split('max-age=')[1].split(';')[0] if 'max-age=' in value else 0) < 31536000
        
        return False
    
    @staticmethod
    def _get_weakness_reason(header: str, value: str) -> str:
        """Get description of why header is weak"""
        if header == 'Strict-Transport-Security':
            return 'HSTS max-age should be at least 1 year (31536000 seconds)'
        elif header == 'X-Frame-Options':
            return f'Weak value "{value}". Should be DENY or SAMEORIGIN'
        elif header == 'X-Content-Type-Options':
            return f'Weak value "{value}". Should be nosniff'
        return 'Misconfigured value'
    
    @staticmethod
    def _get_header_description(header: str) -> str:
        """Get description of what the header does"""
        descriptions = {
            'Content-Security-Policy': 'Prevents XSS, clickjacking, and other code injection attacks',
            'Strict-Transport-Security': 'Forces HTTPS connections and prevents SSL stripping attacks',
            'X-Frame-Options': 'Prevents clickjacking attacks by controlling iframe embedding',
            'X-Content-Type-Options': 'Prevents MIME-sniffing attacks',
            'X-XSS-Protection': 'Enables browser XSS filtering',
            'Referrer-Policy': 'Controls referrer information sent with requests',
            'Permissions-Policy': 'Controls which browser features can be used',
        }
        return descriptions.get(header, 'Security header')

