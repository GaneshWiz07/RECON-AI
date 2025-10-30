"""
Result Merger

Combines and deduplicates results from multiple collectors
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def merge_collector_results(censys_results: List[Dict], shodan_results: List[Dict]) -> List[Dict]:
    """
    Merge results from Censys and Shodan collectors.

    Deduplicates by asset_value and combines data when same asset found in both.

    Args:
        censys_results: Results from Censys collector
        shodan_results: Results from Shodan collector

    Returns:
        Merged and deduplicated list of assets
    """
    # Group results by asset_value
    assets_map = {}

    # Process Censys results
    for asset in censys_results:
        asset_value = asset.get("asset_value")
        if asset_value:
            assets_map[asset_value] = asset

    # Merge with Shodan results
    for asset in shodan_results:
        asset_value = asset.get("asset_value")
        if not asset_value:
            continue

        if asset_value in assets_map:
            # Asset found in both - merge data
            existing = assets_map[asset_value]
            merged = _merge_asset_data(existing, asset)
            assets_map[asset_value] = merged
        else:
            # New asset from Shodan only
            assets_map[asset_value] = asset

    merged_assets = list(assets_map.values())

    logger.info(
        f"Merged {len(censys_results)} Censys + {len(shodan_results)} Shodan results "
        f"into {len(merged_assets)} unique assets"
    )

    return merged_assets


def _merge_asset_data(asset1: Dict, asset2: Dict) -> Dict:
    """
    Merge data from two assets representing the same resource.

    Args:
        asset1: First asset (typically from Censys)
        asset2: Second asset (typically from Shodan)

    Returns:
        Merged asset dictionary
    """
    merged = asset1.copy()

    # Merge open ports (union)
    ports1 = set(asset1.get("open_ports", []))
    ports2 = set(asset2.get("open_ports", []))
    merged["open_ports"] = sorted(list(ports1 | ports2))

    # Merge technologies (union)
    tech1 = set(asset1.get("technologies", []))
    tech2 = set(asset2.get("technologies", []))
    merged["technologies"] = sorted(list(tech1 | tech2))

    # Prefer Censys SSL data (generally more detailed)
    if not merged.get("ssl_cert_expiry") and asset2.get("ssl_cert_expiry"):
        merged["ssl_cert_expiry"] = asset2["ssl_cert_expiry"]
        merged["ssl_cert_issuer"] = asset2.get("ssl_cert_issuer")
        merged["ssl_cert_valid"] = asset2.get("ssl_cert_valid")

    # Prefer Censys HTTP status
    if not merged.get("http_status") and asset2.get("http_status"):
        merged["http_status"] = asset2["http_status"]

    # Prefer Censys server header
    if not merged.get("server_header") and asset2.get("server_header"):
        merged["server_header"] = asset2["server_header"]

    # Merge DNS records
    dns1 = merged.get("dns_records", {})
    dns2 = asset2.get("dns_records", {})
    for record_type, values in dns2.items():
        if record_type not in dns1:
            dns1[record_type] = values
        else:
            # Merge values
            existing = set(dns1[record_type])
            existing.update(values)
            dns1[record_type] = list(existing)
    merged["dns_records"] = dns1

    # Indicate it was found by both
    merged["discovered_via"] = "censys_shodan"

    # Merge raw metadata
    merged["raw_metadata"] = {
        "censys": asset1.get("raw_metadata", {}),
        "shodan": asset2.get("raw_metadata", {})
    }

    return merged
