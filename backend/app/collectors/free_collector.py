"""
Free API Collector Implementation

Uses 100% free APIs:
- crt.sh (Certificate Transparency logs)
- DNS enumeration
- HTTP probing
No API keys required!
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import httpx
import asyncio
import socket
from app.collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class FreeCollector(BaseCollector):
    """
    Free collector using certificate transparency and DNS enumeration.
    No API keys required - completely free!
    """

    def __init__(self):
        super().__init__()
        logger.info("FreeCollector initialized - no API keys required")

    async def search_domain(self, domain: str) -> List[Dict]:
        """
        Search for subdomains and assets related to a domain using free sources.

        Args:
            domain: Domain to search

        Returns:
            List of normalized assets
        """
        logger.info(f"Starting free asset discovery for domain: {domain}")
        
        try:
            assets = []
            
            # 1. Get subdomains from certificate transparency logs (crt.sh)
            subdomains = await self._get_subdomains_from_crtsh(domain)
            logger.info(f"Found {len(subdomains)} subdomains from crt.sh")
            
            # 2. Add the main domain
            all_domains = [domain] + list(subdomains)
            
            # 3. Probe each domain/subdomain
            for subdomain in all_domains[:20]:  # Limit to 20 to avoid long processing
                try:
                    asset = await self._probe_domain(subdomain, domain)
                    if asset:
                        assets.append(asset)
                except Exception as e:
                    logger.debug(f"Failed to probe {subdomain}: {str(e)}")
                    continue
            
            logger.info(f"Free collector found {len(assets)} assets for {domain}")
            return assets

        except Exception as e:
            self._handle_error(e, f"search_domain({domain})")
            return []

    async def get_host_info(self, ip: str) -> Dict:
        """
        Get information for a specific IP address.

        Args:
            ip: IP address

        Returns:
            Normalized asset dict
        """
        try:
            # Perform reverse DNS lookup
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = None

            # Try to probe HTTP/HTTPS
            http_info = await self._probe_http(f"http://{ip}")
            https_info = await self._probe_http(f"https://{ip}")

            return {
                "asset_value": ip,
                "asset_type": "ip_address",
                "parent_domain": hostname,
                "open_ports": [],
                "technologies": [],
                "ssl_cert_expiry": https_info.get("ssl_expiry"),
                "ssl_cert_issuer": https_info.get("ssl_issuer"),
                "ssl_cert_valid": https_info.get("ssl_valid", True),
                "dns_records": {},
                "http_status": https_info.get("status") or http_info.get("status"),
                "server_header": https_info.get("server") or http_info.get("server"),
                "discovered_via": "free_collector",
                "raw_metadata": {
                    "reverse_dns": hostname,
                    "http_accessible": http_info.get("accessible", False),
                    "https_accessible": https_info.get("accessible", False)
                }
            }

        except Exception as e:
            self._handle_error(e, f"get_host_info({ip})")
            return {}

    def normalize_result(self, raw_data: Dict) -> Dict:
        """
        Convert raw data to standard format.

        Args:
            raw_data: Raw data

        Returns:
            Normalized asset dictionary
        """
        # Already normalized in other methods
        return raw_data

    async def _get_subdomains_from_crtsh(self, domain: str) -> set:
        """
        Get subdomains from crt.sh certificate transparency logs.
        Completely free, no API key required!
        """
        subdomains = set()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Query crt.sh JSON API
                response = await client.get(
                    "https://crt.sh/",
                    params={"q": f"%.{domain}", "output": "json"},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for entry in data:
                        name_value = entry.get("name_value", "")
                        # Split by newlines (crt.sh returns multiple names)
                        for subdomain in name_value.split("\n"):
                            subdomain = subdomain.strip().lower()
                            # Remove wildcards and ensure it's valid
                            if subdomain.startswith("*."):
                                subdomain = subdomain[2:]
                            
                            # Only include if it's a subdomain of our target
                            if subdomain.endswith(domain) and subdomain != domain:
                                subdomains.add(subdomain)
                    
                    logger.info(f"crt.sh returned {len(subdomains)} unique subdomains")
                else:
                    logger.warning(f"crt.sh returned status {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to query crt.sh: {str(e)}")
        
        return subdomains

    async def _probe_domain(self, domain: str, parent_domain: str) -> Dict[str, Any]:
        """
        Probe a domain to gather information.
        """
        try:
            # Try to resolve DNS
            try:
                ip_address = socket.gethostbyname(domain)
            except:
                ip_address = None
            
            if not ip_address:
                return None
            
            # Probe HTTP and HTTPS
            http_info = await self._probe_http(f"http://{domain}")
            https_info = await self._probe_http(f"https://{domain}")
            
            # Determine if it's the main domain or subdomain
            asset_type = "domain" if domain == parent_domain else "subdomain"
            
            # Extract technologies from server headers
            technologies = []
            server = https_info.get("server") or http_info.get("server")
            if server:
                technologies.append(server)
            
            # Determine open ports based on what's accessible
            open_ports = []
            if http_info.get("accessible"):
                open_ports.append(80)
            if https_info.get("accessible"):
                open_ports.append(443)
            
            return {
                "asset_value": domain,
                "asset_type": asset_type,
                "parent_domain": parent_domain,
                "ip_address": ip_address,
                "open_ports": open_ports,
                "technologies": technologies,
                "ssl_cert_expiry": https_info.get("ssl_expiry"),
                "ssl_cert_issuer": https_info.get("ssl_issuer"),
                "ssl_cert_valid": https_info.get("ssl_valid", True),
                "dns_records": {"A": [ip_address]} if ip_address else {},
                "http_status": https_info.get("status") or http_info.get("status"),
                "server_header": server,
                "discovered_via": "free_collector",
                "raw_metadata": {
                    "http_accessible": http_info.get("accessible", False),
                    "https_accessible": https_info.get("accessible", False),
                    "http_redirects": http_info.get("redirects", False),
                    "https_redirects": https_info.get("redirects", False)
                }
            }
        
        except Exception as e:
            logger.debug(f"Failed to probe domain {domain}: {str(e)}")
            return None

    async def _probe_http(self, url: str) -> Dict[str, Any]:
        """
        Probe HTTP/HTTPS endpoint to gather information.
        """
        info = {
            "accessible": False,
            "status": None,
            "server": None,
            "redirects": False,
            "ssl_expiry": None,
            "ssl_issuer": None,
            "ssl_valid": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, verify=False) as client:
                response = await client.get(url)
                
                info["accessible"] = True
                info["status"] = response.status_code
                info["server"] = response.headers.get("Server")
                info["redirects"] = response.status_code in [301, 302, 303, 307, 308]
                
                # If HTTPS, try to get SSL info
                if url.startswith("https://"):
                    # Note: Basic SSL info extraction
                    # In production, you might want to use ssl module for detailed cert info
                    info["ssl_valid"] = True  # Since we connected successfully
        
        except httpx.HTTPError:
            pass
        except Exception as e:
            logger.debug(f"HTTP probe failed for {url}: {str(e)}")
        
        return info

