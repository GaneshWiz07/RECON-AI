"""
DNS Misconfiguration Detector

Detects dangling CNAMEs, wildcard records, and DNS misconfigurations
"""

import dns.resolver
import dns.exception
import aiohttp
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DNSMisconfigDetector:
    """Detects DNS misconfigurations and vulnerabilities"""
    
    # Known cloud providers and their error patterns for takeover detection
    TAKEOVER_PATTERNS = {
        'github.io': ['There isn\'t a GitHub Pages site here', 'For root URLs'],
        'herokuapp.com': ['No such app', 'herokucdn.com/error-pages'],
        'azurewebsites.net': ['404 Web Site not found', 'Error 404'],
        'amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
        's3.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
        'cloudfront.net': ['ERROR: The request could not be satisfied'],
        'tumblr.com': ['Whatever you were looking for doesn\'t currently exist'],
        'wordpress.com': ['Do you want to register'],
        'ghost.io': ['The thing you were looking for is no longer here'],
        'pantheon.io': ['404 error unknown site!'],
        'unbounce.com': ['The requested URL was not found on this server'],
    }
    
    @staticmethod
    async def detect(domain: str, timeout: int = 10) -> Dict:
        """
        Detect DNS misconfigurations
        
        Args:
            domain: Target domain
            timeout: Request timeout
            
        Returns:
            Dictionary with DNS findings
        """
        findings = {
            'has_issues': False,
            'issues': [],
            'records': {},
            'severity': 'low',
            'dangling_cname': False,
            'wildcard_dns': False
        }
        
        try:
            # Query DNS records
            records = DNSMisconfigDetector._query_dns_records(domain)
            findings['records'] = records
            
            # Check for dangling CNAMEs
            if 'CNAME' in records:
                for cname in records['CNAME']:
                    is_dangling, provider = await DNSMisconfigDetector._check_dangling_cname(
                        cname, timeout
                    )
                    if is_dangling:
                        findings['issues'].append({
                            'type': 'dangling_cname',
                            'severity': 'critical',
                            'description': f'Dangling CNAME detected: {cname} ({provider})',
                            'cname': cname,
                            'provider': provider,
                            'remediation': 'Remove the CNAME record or reclaim the resource'
                        })
                        findings['has_issues'] = True
                        findings['severity'] = 'critical'
                        findings['dangling_cname'] = True
            
            # Check for wildcard DNS
            is_wildcard = DNSMisconfigDetector._check_wildcard_dns(domain)
            if is_wildcard:
                findings['issues'].append({
                    'type': 'wildcard_dns',
                    'severity': 'medium',
                    'description': 'Wildcard DNS record detected (*.domain)',
                    'remediation': 'Review if wildcard DNS is necessary for your use case'
                })
                findings['has_issues'] = True
                findings['wildcard_dns'] = True
                if findings['severity'] == 'low':
                    findings['severity'] = 'medium'
            
            # Check for missing SPF record
            if 'TXT' not in records or not any('v=spf1' in txt for txt in records.get('TXT', [])):
                findings['issues'].append({
                    'type': 'missing_spf',
                    'severity': 'low',
                    'description': 'Missing SPF record (email spoofing protection)',
                    'remediation': 'Add SPF record to prevent email spoofing'
                })
                findings['has_issues'] = True
            
            # Check for missing DMARC
            try:
                dmarc_domain = f'_dmarc.{domain}'
                dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
                if not any('v=DMARC1' in str(txt) for txt in dmarc_records):
                    findings['issues'].append({
                        'type': 'missing_dmarc',
                        'severity': 'low',
                        'description': 'Missing DMARC record',
                        'remediation': 'Add DMARC record for email authentication'
                    })
                    findings['has_issues'] = True
            except:
                findings['issues'].append({
                    'type': 'missing_dmarc',
                    'severity': 'low',
                    'description': 'Missing DMARC record',
                    'remediation': 'Add DMARC record for email authentication'
                })
                findings['has_issues'] = True
                
        except Exception as e:
            logger.error(f"Error detecting DNS misconfigs for {domain}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _query_dns_records(domain: str) -> Dict[str, List[str]]:
        """Query various DNS record types"""
        records = {}
        record_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS']
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(rdata) for rdata in answers]
            except dns.resolver.NoAnswer:
                continue
            except dns.resolver.NXDOMAIN:
                records['error'] = 'Domain does not exist'
                break
            except Exception:
                continue
        
        return records
    
    @staticmethod
    async def _check_dangling_cname(cname: str, timeout: int) -> tuple:
        """Check if CNAME points to a potentially vulnerable service"""
        cname_lower = cname.lower().rstrip('.')
        
        # Check against known takeover patterns
        for provider, patterns in DNSMisconfigDetector.TAKEOVER_PATTERNS.items():
            if provider in cname_lower:
                # Try to access the CNAME
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f'https://{cname}',
                            timeout=aiohttp.ClientTimeout(total=timeout),
                            allow_redirects=True,
                            ssl=False
                        ) as response:
                            content = await response.text()
                            
                            # Check if response matches takeover patterns
                            for pattern in patterns:
                                if pattern.lower() in content.lower():
                                    return True, provider
                except:
                    # If we can't connect, it might be dangling
                    return True, provider
        
        return False, None
    
    @staticmethod
    def _check_wildcard_dns(domain: str) -> bool:
        """Check if wildcard DNS is configured"""
        try:
            # Try resolving a random subdomain
            import random
            import string
            random_subdomain = ''.join(random.choices(string.ascii_lowercase, k=20))
            test_domain = f'{random_subdomain}.{domain}'
            
            answers = dns.resolver.resolve(test_domain, 'A')
            # If we get an answer for random subdomain, wildcard is likely configured
            return len(list(answers)) > 0
        except:
            return False

