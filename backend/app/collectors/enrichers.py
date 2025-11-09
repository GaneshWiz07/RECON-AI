"""
Asset Enrichers

Additional data enrichment for discovered assets
"""

import logging
from typing import Dict
import dns.resolver
import httpx

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
    Check breach history using HaveIBeenPwned API.

    Args:
        domain: Domain to check

    Returns:
        Number of breaches found
    """
    try:
        url = f"https://haveibeenpwned.com/api/v3/breaches"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"domain": domain},
                headers={"User-Agent": "ReconAI-Scanner"}
            )

            if response.status_code == 404:
                # No breaches found
                return 0

            if response.status_code == 200:
                breaches = response.json()
                breach_count = len(breaches)
                logger.info(f"Found {breach_count} breaches for {domain}")
                return breach_count

            return 0

    except Exception as e:
        logger.warning(f"Breach history check failed for {domain}: {str(e)}")
        return 0


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
