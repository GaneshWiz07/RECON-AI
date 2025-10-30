"""
Censys Collector Implementation

Interfaces with Censys API for asset discovery
"""

import os
import logging
from typing import List, Dict
from datetime import datetime
import httpx
from app.collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class CensysCollector(BaseCollector):
    """
    Censys API collector for discovering hosts and services.
    """

    def __init__(self):
        super().__init__()
        self.api_id = os.getenv("CENSYS_API_ID")
        self.api_secret = os.getenv("CENSYS_API_SECRET")
        self.base_url = "https://search.censys.io/api/v2"

        if not self.api_id or not self.api_secret:
            logger.warning("Censys API credentials not configured")

    async def search_domain(self, domain: str) -> List[Dict]:
        """
        Search Censys for hosts related to a domain.

        Args:
            domain: Domain to search

        Returns:
            List of normalized assets
        """
        if not self.api_id or not self.api_secret:
            logger.warning("Censys credentials missing - skipping")
            return []

        try:
            assets = []
            query = f"services.http.request.host: {domain}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/hosts/search",
                    params={"q": query, "per_page": 100},
                    auth=(self.api_id, self.api_secret)
                )

                if response.status_code == 401:
                    logger.error("Invalid Censys credentials")
                    return []

                if response.status_code == 429:
                    logger.warning("Censys rate limit exceeded")
                    return []

                response.raise_for_status()
                data = response.json()

                results = data.get("result", {}).get("hits", [])

                for hit in results:
                    normalized = self.normalize_result(hit)
                    if normalized:
                        assets.append(normalized)

            logger.info(f"Censys found {len(assets)} assets for {domain}")
            return assets

        except httpx.TimeoutException:
            logger.error(f"Censys search timeout for {domain}")
            return []
        except Exception as e:
            self._handle_error(e, f"search_domain({domain})")
            return []

    async def get_host_info(self, ip: str) -> Dict:
        """
        Get detailed information for a specific IP.

        Args:
            ip: IP address

        Returns:
            Normalized asset dict
        """
        if not self.api_id or not self.api_secret:
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/hosts/{ip}",
                    auth=(self.api_id, self.api_secret)
                )

                response.raise_for_status()
                data = response.json()

                return self.normalize_result(data.get("result", {}))

        except Exception as e:
            self._handle_error(e, f"get_host_info({ip})")
            return {}

    def normalize_result(self, raw_data: Dict) -> Dict:
        """
        Convert Censys response to standard format.

        Args:
            raw_data: Raw Censys host data

        Returns:
            Normalized asset dictionary
        """
        try:
            ip = raw_data.get("ip")
            services = raw_data.get("services", [])

            # Extract open ports
            open_ports = [service.get("port") for service in services if service.get("port")]

            # Extract technologies from service banners
            technologies = []
            server_header = None
            http_status = None
            ssl_cert_expiry = None
            ssl_cert_issuer = None
            ssl_cert_valid = True

            for service in services:
                # HTTP service info
                if "http" in service:
                    http_data = service["http"]
                    response = http_data.get("response", {})
                    headers = response.get("headers", {})

                    if "Server" in headers:
                        server_header = headers["Server"]
                        technologies.append(server_header)

                    http_status = response.get("status_code")

                # TLS/SSL certificate info
                if "tls" in service:
                    tls_data = service["tls"]
                    certificates = tls_data.get("certificates", {})
                    leaf_cert = certificates.get("leaf_data", {})
                    parsed = leaf_cert.get("parsed", {})

                    validity = parsed.get("validity", {})
                    ssl_cert_expiry = validity.get("end")
                    ssl_cert_issuer = parsed.get("issuer", {}).get("common_name", [None])[0]

                    # Check if valid
                    if ssl_cert_expiry:
                        try:
                            expiry_date = datetime.fromisoformat(ssl_cert_expiry.replace('Z', '+00:00'))
                            ssl_cert_valid = expiry_date > datetime.now(expiry_date.tzinfo)
                        except:
                            pass

            # Determine asset type
            asset_type = "ip_address"
            asset_value = ip

            return {
                "asset_value": asset_value,
                "asset_type": asset_type,
                "parent_domain": None,
                "open_ports": open_ports,
                "technologies": technologies,
                "ssl_cert_expiry": ssl_cert_expiry,
                "ssl_cert_issuer": ssl_cert_issuer,
                "ssl_cert_valid": ssl_cert_valid,
                "dns_records": {},
                "http_status": http_status,
                "server_header": server_header,
                "discovered_via": "censys",
                "raw_metadata": {
                    "censys_ip": ip,
                    "services_count": len(services)
                }
            }

        except Exception as e:
            logger.error(f"Failed to normalize Censys result: {str(e)}")
            return {}
