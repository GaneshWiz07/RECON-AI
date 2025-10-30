"""
Shodan Collector Implementation

Interfaces with Shodan API for asset discovery
"""

import os
import logging
from typing import List, Dict
from datetime import datetime
import httpx
from app.collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class ShodanCollector(BaseCollector):
    """
    Shodan API collector for discovering hosts and services.
    """

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("SHODAN_API_KEY")
        self.base_url = "https://api.shodan.io"

        if not self.api_key:
            logger.warning("Shodan API key not configured")

    async def search_domain(self, domain: str) -> List[Dict]:
        """
        Search Shodan for hosts related to a domain.

        Args:
            domain: Domain to search

        Returns:
            List of normalized assets
        """
        if not self.api_key:
            logger.warning("Shodan API key missing - skipping")
            return []

        try:
            assets = []
            query = f"hostname:{domain}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/shodan/host/search",
                    params={"key": self.api_key, "query": query}
                )

                if response.status_code == 401:
                    logger.error("Invalid Shodan API key")
                    return []

                if response.status_code == 429:
                    logger.warning("Shodan rate limit exceeded")
                    return []

                response.raise_for_status()
                data = response.json()

                matches = data.get("matches", [])

                for match in matches:
                    normalized = self.normalize_result(match)
                    if normalized:
                        assets.append(normalized)

            logger.info(f"Shodan found {len(assets)} assets for {domain}")
            return assets

        except httpx.TimeoutException:
            logger.error(f"Shodan search timeout for {domain}")
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
        if not self.api_key:
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/shodan/host/{ip}",
                    params={"key": self.api_key}
                )

                response.raise_for_status()
                data = response.json()

                return self.normalize_result(data)

        except Exception as e:
            self._handle_error(e, f"get_host_info({ip})")
            return {}

    def normalize_result(self, raw_data: Dict) -> Dict:
        """
        Convert Shodan response to standard format.

        Args:
            raw_data: Raw Shodan host data

        Returns:
            Normalized asset dictionary
        """
        try:
            ip = raw_data.get("ip_str")
            port = raw_data.get("port")

            # Extract technologies
            technologies = []
            product = raw_data.get("product")
            version = raw_data.get("version")

            if product:
                tech_string = f"{product}"
                if version:
                    tech_string += f"/{version}"
                technologies.append(tech_string)

            # HTTP info
            http_status = None
            server_header = None
            if "http" in raw_data:
                http_data = raw_data["http"]
                http_status = http_data.get("status")
                server_header = http_data.get("server")
                if server_header and server_header not in technologies:
                    technologies.append(server_header)

            # SSL info
            ssl_cert_expiry = None
            ssl_cert_issuer = None
            ssl_cert_valid = True

            if "ssl" in raw_data:
                ssl_data = raw_data["ssl"]
                cert = ssl_data.get("cert", {})
                ssl_cert_expiry = cert.get("expires")
                ssl_cert_issuer = cert.get("issuer", {}).get("CN")

                if ssl_cert_expiry:
                    try:
                        expiry_timestamp = datetime.fromtimestamp(ssl_cert_expiry)
                        ssl_cert_valid = expiry_timestamp > datetime.now()
                    except:
                        pass

            # Determine asset type
            asset_type = "ip_address"
            asset_value = ip

            return {
                "asset_value": asset_value,
                "asset_type": asset_type,
                "parent_domain": None,
                "open_ports": [port] if port else [],
                "technologies": technologies,
                "ssl_cert_expiry": ssl_cert_expiry,
                "ssl_cert_issuer": ssl_cert_issuer,
                "ssl_cert_valid": ssl_cert_valid,
                "dns_records": {},
                "http_status": http_status,
                "server_header": server_header,
                "discovered_via": "shodan",
                "raw_metadata": {
                    "shodan_ip": ip,
                    "port": port,
                    "transport": raw_data.get("transport")
                }
            }

        except Exception as e:
            logger.error(f"Failed to normalize Shodan result: {str(e)}")
            return {}
