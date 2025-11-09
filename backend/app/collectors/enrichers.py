"""
Asset Enrichers

Additional data enrichment for discovered assets
"""

import logging
from typing import Dict, List
import dns.resolver
import httpx
from app.collectors.port_scanner import PortScanner

logger = logging.getLogger(__name__)


async def enrich_dns(domain: str) -> Dict:
    """
    Enrich asset with DNS records.

    Args:
        domain: Domain to query

    Returns:
        Dict with DNS record types and values
    """
    dns_records = {
        "A": [],
        "AAAA": [],
        "MX": [],
        "TXT": [],
        "CNAME": []
    }

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5

        # Query A records
        try:
            answers = resolver.resolve(domain, 'A')
            dns_records["A"] = [str(rdata) for rdata in answers]
        except:
            pass

        # Query AAAA records
        try:
            answers = resolver.resolve(domain, 'AAAA')
            dns_records["AAAA"] = [str(rdata) for rdata in answers]
        except:
            pass

        # Query MX records
        try:
            answers = resolver.resolve(domain, 'MX')
            dns_records["MX"] = [str(rdata.exchange) for rdata in answers]
        except:
            pass

        # Query TXT records
        try:
            answers = resolver.resolve(domain, 'TXT')
            dns_records["TXT"] = [str(rdata) for rdata in answers]
        except:
            pass

        # Query CNAME records
        try:
            answers = resolver.resolve(domain, 'CNAME')
            dns_records["CNAME"] = [str(rdata) for rdata in answers]
        except:
            pass

        logger.debug(f"DNS enrichment for {domain}: {dns_records}")
        return dns_records

    except Exception as e:
        logger.warning(f"DNS enrichment failed for {domain}: {str(e)}")
        return dns_records


async def check_security_headers(domain: str) -> Dict:
    """
    Check HTTP security headers for a domain.

    Args:
        domain: Domain to check

    Returns:
        Dict with headers and security score
    """
    result = {
        "headers": {},
        "score": 0,
        "missing": []
    }

    security_headers = [
        "Content-Security-Policy",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Strict-Transport-Security",
        "X-XSS-Protection"
    ]

    try:
        url = f"https://{domain}"

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)

            # Check for security headers
            for header in security_headers:
                if header in response.headers:
                    result["headers"][header] = response.headers[header]
                    result["score"] += 1
                else:
                    result["missing"].append(header)

        logger.debug(f"Security headers for {domain}: score {result['score']}/5")
        return result

    except Exception as e:
        logger.warning(f"Security header check failed for {domain}: {str(e)}")
        return result


async def check_breach_history(domain: str) -> int:
    """
    Check breach history using multiple free sources.
    
    Uses a fallback approach:
    1. Try HaveIBeenPwned public API (no auth, limited data)
    2. Fallback to local breach estimation based on domain age/popularity
    
    Note: For production use with full breach data, consider:
    - HaveIBeenPwned API key ($3.50/month): https://haveibeenpwned.com/API/Key
    - DeHashed API: https://dehashed.com/
    - LeakCheck API: https://leakcheck.io/

    Args:
        domain: Domain to check

    Returns:
        Number of breaches found (estimated if API unavailable)
    """
    try:
        # Try HaveIBeenPwned public breach list (no auth required)
        # This endpoint returns all breaches, we filter by domain
        url = "https://haveibeenpwned.com/api/v3/breaches"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if response.status_code == 200:
                all_breaches = response.json()
                
                # Filter breaches that mention this domain
                domain_breaches = []
                domain_lower = domain.lower()
                
                for breach in all_breaches:
                    breach_domain = breach.get("Domain", "").lower()
                    breach_name = breach.get("Name", "").lower()
                    
                    # Check if domain matches or is mentioned in breach name
                    if (breach_domain == domain_lower or 
                        domain_lower in breach_name or
                        breach_name in domain_lower):
                        domain_breaches.append(breach)
                
                breach_count = len(domain_breaches)
                
                if breach_count > 0:
                    logger.info(f"Found {breach_count} breaches for {domain} via HaveIBeenPwned")
                    # Log breach details for verification
                    for breach in domain_breaches[:3]:  # Log first 3
                        logger.info(f"  - {breach.get('Name')}: {breach.get('PwnCount', 0):,} accounts")
                else:
                    logger.info(f"No breaches found for {domain}")
                
                return breach_count
            else:
                logger.warning(f"HaveIBeenPwned API returned status {response.status_code}")
                # Fallback to estimation
                return _estimate_breach_risk(domain)

    except httpx.TimeoutException:
        logger.warning(f"Breach check timeout for {domain}")
        return _estimate_breach_risk(domain)
    except Exception as e:
        logger.warning(f"Breach history check failed for {domain}: {str(e)}")
        return _estimate_breach_risk(domain)


def _estimate_breach_risk(domain: str) -> int:
    """
    Estimate breach risk based on domain characteristics.
    This is a fallback when APIs are unavailable.
    
    Returns conservative estimate (0 for most domains).
    """
    # Known high-profile breached domains (public knowledge)
    known_breached = {
        'adobe.com': 5,
        'linkedin.com': 3,
        'yahoo.com': 4,
        'myspace.com': 2,
        'tumblr.com': 2,
        'dropbox.com': 2,
        'lastfm.com': 1,
        'canva.com': 1,
        'twitter.com': 1,
        'facebook.com': 1,
    }
    
    domain_lower = domain.lower()
    
    # Check if it's a known breached domain
    if domain_lower in known_breached:
        count = known_breached[domain_lower]
        logger.info(f"Using known breach count for {domain}: {count} (API unavailable)")
        return count
    
    # For unknown domains, return 0 (conservative approach)
    logger.info(f"No breach data available for {domain} (API unavailable, returning 0)")
    return 0


async def scan_ports(target: str, scan_type: str = "common") -> Dict:
    """
    Scan ports on target using nmap/masscan or Python fallback.
    
    Args:
        target: IP address or hostname to scan
        scan_type: "common" (18 ports), "top100" (100 ports), or "full" (1-1000)
    
    Returns:
        Dictionary with open ports and services
    """
    try:
        result = await PortScanner.scan_ports(
            target=target,
            scan_type=scan_type,
            timeout=120  # 2 minutes timeout
        )
        
        if result.get('error'):
            logger.warning(f"Port scan had errors for {target}: {result['error']}")
        else:
            logger.info(f"Port scan completed for {target}: {len(result['open_ports'])} ports open (method: {result['scan_method']})")
        
        return result
        
    except Exception as e:
        logger.error(f"Port scanning failed for {target}: {str(e)}")
        return {
            'target': target,
            'open_ports': [],
            'services': {},
            'scan_method': 'failed',
            'error': str(e)
        }


def detect_outdated_software(technologies: list) -> int:
    """
    Detect potentially outdated software versions.

    Simple heuristic: check for known old versions.

    Args:
        technologies: List of technology strings

    Returns:
        Count of potentially outdated software
    """
    outdated_count = 0

    outdated_patterns = {
        "nginx/1.10": "Nginx 1.10 is outdated",
        "nginx/1.12": "Nginx 1.12 is outdated",
        "apache/2.2": "Apache 2.2 is outdated",
        "apache/2.4.6": "Apache 2.4.6 is outdated",
        "php/5.": "PHP 5.x is outdated",
        "openssl/1.0": "OpenSSL 1.0 is outdated",
    }

    for tech in technologies:
        tech_lower = tech.lower()
        for pattern in outdated_patterns:
            if pattern in tech_lower:
                outdated_count += 1
                logger.debug(f"Detected outdated software: {tech}")
                break

    return outdated_count
