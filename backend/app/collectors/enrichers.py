"""
Asset Enrichers

Additional data enrichment for discovered assets
"""

import logging
import os
import asyncio
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
    Check breach history using XposedOrNot API (free public API).

    Args:
        domain: Domain to check

    Returns:
        Number of breaches found
    """
    try:
        # Clean domain (remove protocol, www, etc.)
        clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
        clean_domain = clean_domain.replace('www.', '').split(':')[0]
        
        # XposedOrNot API endpoint for domain breach checking
        # Check common email addresses associated with the domain
        # Common email patterns to check: admin, info, contact, support, noreply
        common_emails = [
            f"admin@{clean_domain}",
            f"info@{clean_domain}",
            f"contact@{clean_domain}",
            f"support@{clean_domain}",
            f"noreply@{clean_domain}"
        ]
        
        breach_count = 0
        checked_emails = set()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for email in common_emails:
                try:
                    # XposedOrNot API endpoint for email breach checking
                    url = f"https://api.xposedornot.com/v1/check-email/{email}"
                    
                    response = await client.get(
                        url,
                        headers={
                            "User-Agent": "ReconAI-Scanner",
                            "Accept": "application/json"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Check if email has been exposed
                        if isinstance(data, dict):
                            # XposedOrNot API returns {"breaches": [["breach1", "breach2", ...]]} for exposed emails
                            # Or {"Error": "Not found", "email": null} for non-exposed emails
                            if "breaches" in data and isinstance(data["breaches"], list) and len(data["breaches"]) > 0:
                                # breaches is a nested list: [["breach1", "breach2", ...]]
                                breaches_list = data["breaches"][0] if isinstance(data["breaches"][0], list) else data["breaches"]
                                breach_count += len(breaches_list)
                                checked_emails.add(email)
                                logger.debug(f"Found {len(breaches_list)} breaches for {email}")
                            elif "Error" in data and data.get("Error") == "Not found":
                                # No breaches found for this email
                                logger.debug(f"No breaches found for {email}")
                                continue
                            elif data.get("exposed", False) or data.get("breach_count", 0) > 0:
                                # Fallback for other response formats
                                breach_count += data.get("breach_count", 1)
                                checked_emails.add(email)
                                logger.debug(f"Found breach for {email}: {data.get('breach_count', 1)} breaches")
                        elif isinstance(data, list) and len(data) > 0:
                            # Response is a list of breaches
                            breach_count += len(data)
                            checked_emails.add(email)
                            logger.debug(f"Found {len(data)} breaches for {email}")
                    elif response.status_code == 404:
                        # No breaches found for this email
                        continue
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited by XposedOrNot API for {email}")
                        break
                    else:
                        logger.debug(f"Unexpected status {response.status_code} from XposedOrNot API for {email}")
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.5)
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        continue
                    logger.debug(f"HTTP error checking {email}: {str(e)}")
                except Exception as e:
                    logger.debug(f"Error checking {email}: {str(e)}")
                    continue
        
        if breach_count > 0:
            logger.info(f"Found {breach_count} total breaches for domain {clean_domain} (checked {len(checked_emails)} emails)")
        else:
            logger.debug(f"No breaches found for domain {clean_domain}")
        
        return breach_count

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
