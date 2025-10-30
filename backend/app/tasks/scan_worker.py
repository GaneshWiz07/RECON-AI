"""
Scan Worker

Background worker that executes asset discovery scans
"""

import logging
import asyncio
from datetime import datetime
from app.core.database import get_collection
from app.collectors.free_collector import FreeCollector
from app.collectors.enrichers import (
    enrich_dns,
    check_security_headers,
    check_breach_history,
    detect_outdated_software
)
from app.ml.predict import predict_risk_score, get_risk_level
from app.detectors import (
    WebHeaderAnalyzer,
    SSLInspector,
    DNSMisconfigDetector,
    CloudBucketChecker,
    SecurityFileChecker,
    OpenDirectoryDetector
)

logger = logging.getLogger(__name__)


async def run_misconfiguration_detectors(asset_value: str) -> dict:
    """
    Run all misconfiguration detectors on an asset
    
    Args:
        asset_value: The asset URL/domain to check
        
    Returns:
        Dictionary with all misconfiguration findings
    """
    misconfigurations = {
        'total_issues': 0,
        'severity': 'low',
        'web_headers': {},
        'ssl': {},
        'dns': {},
        'cloud_buckets': {},
        'security_files': {},
        'open_directories': {}
    }
    
    try:
        # Run all detectors concurrently for better performance
        results = await asyncio.gather(
            WebHeaderAnalyzer.analyze(asset_value),
            SSLInspector.inspect(asset_value),
            DNSMisconfigDetector.detect(asset_value),
            CloudBucketChecker.check(asset_value),
            SecurityFileChecker.check(asset_value),
            OpenDirectoryDetector.detect(asset_value),
            return_exceptions=True
        )
        
        # Unpack results
        web_headers, ssl, dns, cloud_buckets, security_files, open_dirs = results
        
        # Process each detector result
        if not isinstance(web_headers, Exception):
            misconfigurations['web_headers'] = web_headers
            if web_headers.get('has_issues'):
                misconfigurations['total_issues'] += len(web_headers.get('missing_headers', []))
                if web_headers['severity'] in ['critical', 'high']:
                    misconfigurations['severity'] = web_headers['severity']
        
        if not isinstance(ssl, Exception):
            misconfigurations['ssl'] = ssl
            if ssl.get('has_issues'):
                misconfigurations['total_issues'] += len(ssl.get('issues', []))
                if ssl['severity'] == 'critical' or (ssl['severity'] == 'high' and misconfigurations['severity'] != 'critical'):
                    misconfigurations['severity'] = ssl['severity']
        
        if not isinstance(dns, Exception):
            misconfigurations['dns'] = dns
            if dns.get('has_issues'):
                misconfigurations['total_issues'] += len(dns.get('issues', []))
                if dns['severity'] == 'critical':
                    misconfigurations['severity'] = 'critical'
        
        if not isinstance(cloud_buckets, Exception):
            misconfigurations['cloud_buckets'] = cloud_buckets
            if cloud_buckets.get('has_issues'):
                misconfigurations['total_issues'] += len(cloud_buckets.get('buckets', []))
                misconfigurations['severity'] = 'critical'
        
        if not isinstance(security_files, Exception):
            misconfigurations['security_files'] = security_files
            if security_files.get('has_issues'):
                misconfigurations['total_issues'] += len(security_files.get('sensitive_exposed', []))
                if security_files['severity'] == 'critical':
                    misconfigurations['severity'] = 'critical'
        
        if not isinstance(open_dirs, Exception):
            misconfigurations['open_directories'] = open_dirs
            if open_dirs.get('has_issues'):
                misconfigurations['total_issues'] += len(open_dirs.get('open_directories', []))
                if open_dirs['severity'] in ['critical', 'high'] and misconfigurations['severity'] not in ['critical']:
                    misconfigurations['severity'] = open_dirs['severity']
        
    except Exception as e:
        logger.error(f"Error running misconfiguration detectors: {str(e)}")
        misconfigurations['error'] = str(e)
    
    return misconfigurations


def execute_scan(scan_id: str, domain: str, user_id: str):
    """
    Execute asset discovery scan (sync wrapper).

    Args:
        scan_id: Scan identifier
        domain: Domain to scan
        user_id: User ID
    """
    # Run async scan in sync context
    asyncio.run(_execute_scan_async(scan_id, domain, user_id))


async def _execute_scan_async(scan_id: str, domain: str, user_id: str):
    """
    Execute asset discovery scan asynchronously.

    Process:
    1. Update scan status to "running"
    2. Run free collector (crt.sh + DNS)
    3. Enrich each asset with DNS, security headers, breach data
    4. Calculate risk scores
    5. Save assets to MongoDB
    6. Update scan status to "completed"
    """
    logger.info(f"Starting scan {scan_id} for domain {domain}")

    scans_collection = get_collection("scans")
    assets_collection = get_collection("assets")

    try:
        # Update scan status to running
        await scans_collection.update_one(
            {"scan_id": scan_id},
            {
                "$set": {
                    "scan_status": "running",
                    "started_at": datetime.utcnow()
                }
            }
        )

        # Initialize free collector (no API keys needed!)
        collector = FreeCollector()

        # Run collector
        logger.info(f"Running free collector for {domain}")
        collector_results = await collector.search_domain(domain)

        # Handle collector failure
        if isinstance(collector_results, Exception):
            logger.error(f"Free collector failed: {str(collector_results)}")
            collector_results = []

        # Use results directly
        merged_assets = collector_results

        logger.info(f"Enriching {len(merged_assets)} assets")

        # Enrich and save each asset
        assets_saved = 0
        for asset_data in merged_assets:
            try:
                # Enrich with DNS records
                dns_records = await enrich_dns(asset_data.get("asset_value", domain))
                asset_data["dns_records"] = dns_records

                # Check security headers
                headers_data = await check_security_headers(domain)
                asset_data["http_security_headers_score"] = headers_data["score"]
                asset_data["missing_security_headers"] = headers_data["missing"]

                # Check breach history
                breach_count = await check_breach_history(domain)
                asset_data["breach_history_count"] = breach_count

                # Detect outdated software
                outdated_count = detect_outdated_software(asset_data.get("technologies", []))
                asset_data["outdated_software_count"] = outdated_count

                # Run misconfiguration detectors
                misconfigurations = await run_misconfiguration_detectors(asset_data.get("asset_value", domain))
                asset_data["misconfigurations"] = misconfigurations

                # Calculate risk score using ML model
                ml_risk_score, ml_risk_class = predict_risk_score(asset_data)
                
                if ml_risk_score is not None:
                    # Use ML prediction
                    risk_score = ml_risk_score
                    logger.info(f"ML predicted risk score: {risk_score} for {asset_data.get('asset_value')}")
                else:
                    # Fallback to basic calculation if ML model not available
                    risk_score = _calculate_basic_risk_score(asset_data)
                    logger.warning(f"Using basic risk calculation (ML model not loaded) for {asset_data.get('asset_value')}")
                
                asset_data["risk_score"] = risk_score
                asset_data["risk_level"] = get_risk_level(risk_score)
                asset_data["risk_factors"] = _extract_risk_factors(asset_data)

                # Generate asset ID
                asset_id = f"ast_{datetime.utcnow().timestamp()}_{assets_saved}"

                # Prepare asset document
                asset_doc = {
                    "asset_id": asset_id,
                    "user_id": user_id,
                    "workspace_id": user_id,
                    **asset_data,
                    "parent_domain": domain,
                    "discovered_at": datetime.utcnow(),
                    "last_scanned_at": datetime.utcnow(),
                    "rescan_enabled": False,
                    "rescan_frequency": "never",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }

                # Upsert asset (update if exists, insert if new)
                await assets_collection.update_one(
                    {"user_id": user_id, "asset_value": asset_data["asset_value"]},
                    {"$set": asset_doc},
                    upsert=True
                )

                assets_saved += 1

            except Exception as e:
                logger.error(f"Failed to process asset: {str(e)}")
                continue

        # Update scan record
        await scans_collection.update_one(
            {"scan_id": scan_id},
            {
                "$set": {
                    "scan_status": "completed",
                    "completed_at": datetime.utcnow(),
                    "assets_found": assets_saved,
                    "duration_seconds": (datetime.utcnow() - (await scans_collection.find_one({"scan_id": scan_id}))["started_at"]).total_seconds()
                }
            }
        )

        logger.info(f"Scan {scan_id} completed: {assets_saved} assets saved")

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {str(e)}")

        # Update scan status to failed
        await scans_collection.update_one(
            {"scan_id": scan_id},
            {
                "$set": {
                    "scan_status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.utcnow()
                }
            }
        )


def _calculate_basic_risk_score(asset: dict) -> int:
    """
    Calculate basic risk score (simple heuristic until ML model in Phase 3).

    Args:
        asset: Asset data dictionary

    Returns:
        Risk score 0-100
    """
    score = 0

    # Open ports (+3 each, max 30)
    open_ports = asset.get("open_ports", [])
    score += min(len(open_ports) * 3, 30)

    # SSH open (+15)
    if 22 in open_ports:
        score += 15

    # Database ports open (+30)
    db_ports = {3306, 5432, 27017, 6379}
    if any(port in db_ports for port in open_ports):
        score += 30

    # Outdated software (+8 each)
    score += asset.get("outdated_software_count", 0) * 8

    # Breach history (+5 each)
    score += asset.get("breach_history_count", 0) * 5

    # Missing security headers (+4 each)
    score += len(asset.get("missing_security_headers", [])) * 4

    # Invalid/expired SSL (+25)
    if not asset.get("ssl_cert_valid", True):
        score += 25

    return min(score, 100)


def _get_risk_level(score: int) -> str:
    """
    Convert risk score to level.

    Args:
        score: Risk score 0-100

    Returns:
        Risk level: low, medium, high, critical
    """
    if score >= 86:
        return "critical"
    elif score >= 61:
        return "high"
    elif score >= 31:
        return "medium"
    else:
        return "low"


def _extract_risk_factors(asset: dict) -> list:
    """
    Extract human-readable risk factors.

    Args:
        asset: Asset data

    Returns:
        List of risk factor strings
    """
    factors = []

    open_ports = asset.get("open_ports", [])

    if 22 in open_ports:
        factors.append("open_port_22")

    if 3389 in open_ports:
        factors.append("open_port_3389_rdp")

    db_ports = {3306, 5432, 27017, 6379}
    if any(port in db_ports for port in open_ports):
        factors.append("exposed_database")

    if not asset.get("ssl_cert_valid", True):
        factors.append("expired_ssl_certificate")

    if asset.get("outdated_software_count", 0) > 0:
        factors.append("outdated_software")

    if asset.get("breach_history_count", 0) > 0:
        factors.append("breach_history")

    if len(asset.get("missing_security_headers", [])) >= 3:
        factors.append("missing_security_headers")

    return factors
