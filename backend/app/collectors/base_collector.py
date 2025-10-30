"""
Base Collector Abstract Class

Defines the interface for all asset collectors (Censys, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for asset collectors.

    All collectors must implement search_domain() and get_host_info() methods.
    """

    def __init__(self):
        """Initialize collector with API credentials."""
        pass

    @abstractmethod
    async def search_domain(self, domain: str) -> List[Dict]:
        """
        Search for assets related to a domain.

        Args:
            domain: Domain to search for

        Returns:
            List of normalized asset dictionaries

        Standard asset format:
        {
            "asset_value": "api.example.com",
            "asset_type": "subdomain",  # or "domain", "ip_address"
            "parent_domain": "example.com",
            "open_ports": [22, 80, 443],
            "technologies": ["Nginx/1.21.0", "React"],
            "ssl_cert_expiry": "2026-05-15T00:00:00Z",
            "ssl_cert_issuer": "Let's Encrypt",
            "ssl_cert_valid": True,
            "dns_records": {
                "A": ["192.168.1.4"],
                "AAAA": [],
                "MX": ["mail.example.com"]
            },
            "http_status": 200,
            "server_header": "nginx/1.21.0",
            "discovered_via": "censys",
            "raw_metadata": {}
        }
        """
        pass

    @abstractmethod
    async def get_host_info(self, ip: str) -> Dict:
        """
        Get detailed information for a specific host/IP.

        Args:
            ip: IP address to query

        Returns:
            Normalized asset dictionary
        """
        pass

    @abstractmethod
    def normalize_result(self, raw_data: Dict) -> Dict:
        """
        Convert raw API response to standard asset format.

        Args:
            raw_data: Raw data from collector API

        Returns:
            Normalized asset dictionary
        """
        pass

    def _handle_error(self, error: Exception, context: str) -> None:
        """
        Handle collector errors with logging.

        Args:
            error: Exception that occurred
            context: Context string for logging
        """
        logger.error(f"{self.__class__.__name__} error in {context}: {str(error)}")
