"""
Analytics API Routes

Provides dashboard statistics, risk trends, and insights
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Query
from app.core.database import get_collection
from app.middleware.auth import get_current_user
from app.services.groq_service import generate_batch_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(request: Request):
    """
    Get dashboard overview statistics.

    Returns key metrics for dashboard cards.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")
        scans_collection = get_collection("scans")

        # Count total assets
        total_assets = await assets_collection.count_documents({"user_id": uid})

        # Count assets by risk level
        assets_by_risk = {
            "low": await assets_collection.count_documents({"user_id": uid, "risk_level": "low"}),
            "medium": await assets_collection.count_documents({"user_id": uid, "risk_level": "medium"}),
            "high": await assets_collection.count_documents({"user_id": uid, "risk_level": "high"}),
            "critical": await assets_collection.count_documents({"user_id": uid, "risk_level": "critical"}),
        }

        # Count total scans
        total_scans = await scans_collection.count_documents({"user_id": uid})

        # Calculate overall risk score (average)
        pipeline = [
            {"$match": {"user_id": uid}},
            {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
        ]
        result = await assets_collection.aggregate(pipeline).to_list(length=1)
        overall_risk_score = int(result[0]["avg_risk"]) if result else 0

        # Determine overall risk level
        if overall_risk_score >= 86:
            overall_risk_level = "critical"
        elif overall_risk_score >= 61:
            overall_risk_level = "high"
        elif overall_risk_score >= 31:
            overall_risk_level = "medium"
        else:
            overall_risk_level = "low"

        # Calculate 7-day changes using historical data
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
        
        # Calculate risk score change (compare current avg vs 7 days ago)
        current_avg_pipeline = [
            {"$match": {"user_id": uid}},
            {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
        ]
        current_avg_result = await assets_collection.aggregate(current_avg_pipeline).to_list(length=1)
        current_avg_risk = current_avg_result[0]["avg_risk"] if current_avg_result and current_avg_result[0].get("avg_risk") else 0
        
        # Get assets discovered 7-14 days ago for comparison
        old_assets_pipeline = [
            {
                "$match": {
                    "user_id": uid,
                    "discovered_at": {"$gte": fourteen_days_ago, "$lt": seven_days_ago}
                }
            },
            {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
        ]
        old_avg_result = await assets_collection.aggregate(old_assets_pipeline).to_list(length=1)
        old_avg_risk = old_avg_result[0]["avg_risk"] if old_avg_result and old_avg_result[0].get("avg_risk") else current_avg_risk
        
        # Calculate change percentage
        if old_avg_risk > 0:
            risk_score_change_7d = round(((current_avg_risk - old_avg_risk) / old_avg_risk) * 100, 1)
        else:
            risk_score_change_7d = 0.0
        
        # Calculate assets change (new assets in last 7 days)
        assets_7d_ago = await assets_collection.count_documents({
            "user_id": uid,
            "discovered_at": {"$lt": seven_days_ago}
        })
        assets_change_7d = round(((total_assets - assets_7d_ago) / max(assets_7d_ago, 1)) * 100, 1) if assets_7d_ago > 0 else (total_assets * 100.0)
        
        # Calculate scans change (scans in last 7 days vs previous 7 days)
        scans_7d_ago = await scans_collection.count_documents({
            "user_id": uid,
            "created_at": {"$lt": seven_days_ago}
        })
        scans_previous_7d = await scans_collection.count_documents({
            "user_id": uid,
            "created_at": {"$gte": fourteen_days_ago, "$lt": seven_days_ago}
        })
        if scans_previous_7d > 0:
            scans_change_7d = round(((total_scans - scans_7d_ago - scans_previous_7d) / scans_previous_7d) * 100, 1)
        else:
            scans_change_7d = (total_scans - scans_7d_ago) * 100.0 if (total_scans - scans_7d_ago) > 0 else 0.0

        # Count new critical alerts (last 7 days)
        new_critical_alerts = await assets_collection.count_documents({
            "user_id": uid,
            "risk_level": "critical",
            "discovered_at": {"$gte": seven_days_ago}
        })

        # Count open vulnerabilities (high + critical)
        open_vulnerabilities = assets_by_risk["high"] + assets_by_risk["critical"]

        return {
            "data": {
                "overall_risk_score": overall_risk_score,
                "overall_risk_level": overall_risk_level,
                "risk_score_change_7d": risk_score_change_7d,
                "discovered_assets": total_assets,
                "assets_change_7d": assets_change_7d,
                "total_scans": total_scans,
                "scans_change_7d": scans_change_7d,
                "new_critical_alerts": new_critical_alerts,
                "open_vulnerabilities": open_vulnerabilities,
                "assets_by_risk": assets_by_risk
            }
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        return {
            "data": {
                "overall_risk_score": 0,
                "overall_risk_level": "low",
                "discovered_assets": 0,
                "total_scans": 0,
                "new_critical_alerts": 0,
                "open_vulnerabilities": 0,
                "assets_by_risk": {"low": 0, "medium": 0, "high": 0, "critical": 0}
            }
        }


@router.get("/risk-trend")
async def get_risk_trend(
    request: Request,
    days: int = Query(30, ge=1, le=90)
):
    """
    Get risk score trend over time based on asset risk scores.

    Args:
        days: Number of days to retrieve (1-90)

    Returns:
        Daily risk score averages
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")
        scans_collection = get_collection("scans")

        # Get scans from last N days
        start_date = datetime.utcnow() - timedelta(days=days)

        # Method 1: Aggregate by scan completion dates with asset risk scores
        scan_pipeline = [
            {
                "$match": {
                    "user_id": uid,
                    "scan_status": "completed",
                    "completed_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$completed_at"
                        }
                    },
                    "scan_date": {"$first": "$completed_at"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        scan_results = await scans_collection.aggregate(scan_pipeline).to_list(length=days)
        
        # Get all assets for this user
        all_assets = await assets_collection.find({"user_id": uid}).to_list(length=None)
        
        trend = []
        
        if scan_results and all_assets:
            # We have completed scans - calculate average risk for each scan date
            # For each scan date, use assets that existed at that time (discovered_at <= scan_date)
            for scan_item in scan_results:
                date_str = scan_item["_id"]
                scan_date = scan_item.get("scan_date")
                
                if scan_date:
                    # Filter assets that existed before or on this scan date
                    assets_at_time = [
                        asset for asset in all_assets
                        if asset.get("discovered_at") and asset.get("discovered_at") <= scan_date
                    ]
                    
                    if assets_at_time:
                        avg_risk = sum(asset.get("risk_score", 0) for asset in assets_at_time) / len(assets_at_time)
                        trend.append({
                            "date": date_str,
                            "risk_score": round(avg_risk, 1)
                        })
                    else:
                        # No assets at this time, use current average
                        avg_risk = sum(asset.get("risk_score", 0) for asset in all_assets) / len(all_assets)
                        trend.append({
                            "date": date_str,
                            "risk_score": round(avg_risk, 1)
                        })
        elif all_assets:
            # No scans yet, but we have assets - show current state
            avg_risk = sum(asset.get("risk_score", 0) for asset in all_assets) / len(all_assets)
            
            # Generate points for the requested days showing current average
            for i in range(min(days, 30)):  # Limit to 30 days max for performance
                date = datetime.utcnow() - timedelta(days=(min(days, 30) - 1 - i))
                date_str = date.strftime("%Y-%m-%d")
                trend.append({
                    "date": date_str,
                    "risk_score": round(avg_risk, 1)
                })
        
        # If we have very few data points but have assets, fill in the trend
        if len(trend) == 1 and all_assets:
            single_point = trend[0]
            trend = []
            for i in range(min(days, 30)):
                date = datetime.utcnow() - timedelta(days=(min(days, 30) - 1 - i))
                date_str = date.strftime("%Y-%m-%d")
                trend.append({
                    "date": date_str,
                    "risk_score": single_point["risk_score"]
                })

        return {"data": {"trend": trend}}

    except Exception as e:
        logger.error(f"Failed to get risk trend: {str(e)}")
        return {"data": {"trend": []}}


@router.get("/top-risky-assets")
async def get_top_risky_assets(
    request: Request,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get highest risk assets.

    Args:
        limit: Number of assets to return (1-50)

    Returns:
        List of top risky assets
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        cursor = assets_collection.find(
            {"user_id": uid}
        ).sort("risk_score", -1).limit(limit)

        assets = await cursor.to_list(length=limit)

        # Remove MongoDB _id
        for asset in assets:
            asset.pop("_id", None)

        return {"data": {"assets": assets}}

    except Exception as e:
        logger.error(f"Failed to get top risky assets: {str(e)}")
        return {"data": {"assets": []}}


@router.get("/asset-distribution")
async def get_asset_distribution(request: Request):
    """
    Get asset distribution by type (domain, subdomain, ip_address).

    Returns:
        Asset counts by type for bar chart
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        # Count assets by type
        distribution = []
        
        for asset_type in ["domain", "subdomain", "ip_address"]:
            count = await assets_collection.count_documents({
                "user_id": uid,
                "asset_type": asset_type
            })
            if count > 0:  # Only include types with assets
                distribution.append({
                    "type": asset_type.replace("_", " ").title(),
                    "count": count,
                    "asset_type": asset_type
                })

        return {"data": {"distribution": distribution}}

    except Exception as e:
        logger.error(f"Failed to get asset distribution: {str(e)}")
        return {"data": {"distribution": []}}


@router.get("/risk-factors")
async def get_risk_factors(request: Request):
    """
    Get risk factors analysis - what's causing risk scores.

    Returns:
        Percentage of assets affected by each risk factor
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        # Get total asset count
        total_assets = await assets_collection.count_documents({"user_id": uid})
        
        if total_assets == 0:
            return {"data": {"factors": [], "total_assets": 0}}

        factors = []

        # Count assets with open SSH port (22) - MongoDB checks if value is in array
        ssh_count = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": {"$in": [22]}  # More explicit array check
        })
        if ssh_count > 0:
            factors.append({
                "name": "SSH Exposed",
                "count": ssh_count,
                "percentage": round((ssh_count / total_assets) * 100, 1)
            })

        # Count assets with database ports
        db_count = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": {"$in": [3306, 5432, 27017, 6379]}
        })
        if db_count > 0:
            factors.append({
                "name": "Database Exposed",
                "count": db_count,
                "percentage": round((db_count / total_assets) * 100, 1)
            })

        # Count assets with outdated software
        outdated_count = await assets_collection.count_documents({
            "user_id": uid,
            "outdated_software_count": {"$gt": 0}
        })
        if outdated_count > 0:
            factors.append({
                "name": "Outdated Software",
                "count": outdated_count,
                "percentage": round((outdated_count / total_assets) * 100, 1)
            })

        # Count assets with invalid SSL
        ssl_count = await assets_collection.count_documents({
            "user_id": uid,
            "ssl_cert_valid": False
        })
        if ssl_count > 0:
            factors.append({
                "name": "Invalid SSL",
                "count": ssl_count,
                "percentage": round((ssl_count / total_assets) * 100, 1)
            })

        # Count assets with missing security headers (check both top-level and nested)
        headers_count = await assets_collection.count_documents({
            "user_id": uid,
            "$or": [
                {"http_security_headers_score": {"$lt": 3}},
                {"misconfigurations.web_headers.has_issues": True}
            ]
        })
        if headers_count > 0:
            factors.append({
                "name": "Missing Security Headers",
                "count": headers_count,
                "percentage": round((headers_count / total_assets) * 100, 1)
            })

        # Count assets with SSL/TLS issues (check nested misconfigurations)
        ssl_issues_count = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.ssl.has_issues": {"$eq": True}
        })
        if ssl_issues_count > 0:
            factors.append({
                "name": "SSL/TLS Issues",
                "count": ssl_issues_count,
                "percentage": round((ssl_issues_count / total_assets) * 100, 1)
            })

        # Count assets with DNS misconfigurations
        dns_issues_count = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.dns.has_issues": {"$eq": True}
        })
        if dns_issues_count > 0:
            factors.append({
                "name": "DNS Misconfigurations",
                "count": dns_issues_count,
                "percentage": round((dns_issues_count / total_assets) * 100, 1)
            })

        # Count assets with exposed cloud buckets
        cloud_buckets_count = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.cloud_buckets.has_issues": {"$eq": True}
        })
        if cloud_buckets_count > 0:
            factors.append({
                "name": "Exposed Cloud Storage",
                "count": cloud_buckets_count,
                "percentage": round((cloud_buckets_count / total_assets) * 100, 1)
            })

        # Count assets with exposed sensitive files
        security_files_count = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.security_files.has_issues": {"$eq": True}
        })
        if security_files_count > 0:
            factors.append({
                "name": "Exposed Sensitive Files",
                "count": security_files_count,
                "percentage": round((security_files_count / total_assets) * 100, 1)
            })

        # Count assets with open directories
        open_dirs_count = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.open_directories.has_issues": {"$eq": True}
        })
        if open_dirs_count > 0:
            factors.append({
                "name": "Open Directories",
                "count": open_dirs_count,
                "percentage": round((open_dirs_count / total_assets) * 100, 1)
            })

        # Count assets with breach history
        breach_count = await assets_collection.count_documents({
            "user_id": uid,
            "breach_history_count": {"$gt": 0}
        })
        if breach_count > 0:
            factors.append({
                "name": "Breach History",
                "count": breach_count,
                "percentage": round((breach_count / total_assets) * 100, 1)
            })

        # Sort by percentage descending
        factors.sort(key=lambda x: x["percentage"], reverse=True)

        return {"data": {"factors": factors[:8], "total_assets": total_assets}}  # Return top 8 with total

    except Exception as e:
        logger.error(f"Failed to get risk factors: {str(e)}")
        return {"data": {"factors": [], "total_assets": 0}}


@router.get("/security-insights")
async def get_security_insights(request: Request):
    """
    Get actionable security insights based on real asset data.

    Returns:
        Personalized security recommendations
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")
        scans_collection = get_collection("scans")

        insights = []

        # Get total assets and high-risk assets
        total_assets = await assets_collection.count_documents({"user_id": uid})
        high_risk_assets = await assets_collection.count_documents({
            "user_id": uid,
            "risk_score": {"$gte": 70}
        })

        # Get last scan info
        last_scan = await scans_collection.find_one(
            {"user_id": uid, "scan_status": "completed"},
            sort=[("completed_at", -1)]
        )

        # Insight 1: High-Risk Assets
        if high_risk_assets > 0:
            insights.append({
                "type": "critical",
                "title": "Critical Assets Detected",
                "message": f"{high_risk_assets} asset(s) have risk scores above 70 and require immediate attention.",
                "priority": "critical",
                "stats": {
                    "count": high_risk_assets,
                    "total": total_assets
                }
            })

        # Insight 3: Exposed Services
        ssh_exposed = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": {"$in": [22]}  # More explicit array check
        })
        
        db_exposed = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": {"$in": [3306, 5432, 27017, 6379]}  # Check if any DB port is in array
        })

        if ssh_exposed > 0 or db_exposed > 0:
            exposed_services = []
            if ssh_exposed > 0:
                exposed_services.append(f"{ssh_exposed} SSH")
            if db_exposed > 0:
                exposed_services.append(f"{db_exposed} Database")
            
            insights.append({
                "type": "warning",
                "title": "Exposed Services",
                "message": f"Found {', '.join(exposed_services)} port(s) exposed to the internet. Review access controls.",
                "priority": "high",
                "stats": {
                    "ssh": ssh_exposed,
                    "database": db_exposed
                }
            })

        # Insight 3: SSL/TLS Status (check both top-level and nested)
        invalid_ssl_top = await assets_collection.count_documents({
            "user_id": uid,
            "ssl_cert_valid": False
        })
        
        ssl_issues_nested = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.ssl.has_issues": {"$eq": True}
        })
        
        invalid_ssl = max(invalid_ssl_top, ssl_issues_nested)

        if invalid_ssl > 0:
            insights.append({
                "type": "warning",
                "title": "SSL Certificate Issues",
                "message": f"{invalid_ssl} asset(s) have SSL/TLS certificate issues. This affects trust and security.",
                "priority": "high",
                "stats": {
                    "count": invalid_ssl
                }
            })

        # Insight 4: Security Headers (check both top-level and nested)
        missing_headers_top = await assets_collection.count_documents({
            "user_id": uid,
            "http_security_headers_score": {"$lt": 3}
        })
        
        missing_headers_nested = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.web_headers.has_issues": {"$eq": True}
        })
        
        missing_headers = max(missing_headers_top, missing_headers_nested)

        if missing_headers > 0:
            percentage = round((missing_headers / total_assets) * 100) if total_assets > 0 else 0
            insights.append({
                "type": "info",
                "title": "Security Headers",
                "message": f"{percentage}% of assets are missing critical security headers. Consider implementing CSP, HSTS, and X-Frame-Options.",
                "priority": "medium",
                "stats": {
                    "count": missing_headers,
                    "percentage": percentage
                }
            })

        # Insight 5: DNS Misconfigurations
        dns_issues = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.dns.has_issues": {"$eq": True}
        })
        
        if dns_issues > 0:
            percentage = round((dns_issues / total_assets) * 100) if total_assets > 0 else 0
            insights.append({
                "type": "warning",
                "title": "DNS Misconfigurations",
                "message": f"{dns_issues} asset(s) have DNS misconfigurations (missing SPF, DMARC, or other DNS records). This can lead to email spoofing and security issues.",
                "priority": "high",
                "stats": {
                    "count": dns_issues,
                    "percentage": percentage
                }
            })

        # Insight 6: Exposed Cloud Storage
        cloud_buckets = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.cloud_buckets.has_issues": {"$eq": True}
        })
        
        if cloud_buckets > 0:
            insights.append({
                "type": "critical",
                "title": "Exposed Cloud Storage",
                "message": f"{cloud_buckets} asset(s) have exposed cloud storage buckets. This is a critical security risk that can lead to data breaches.",
                "priority": "critical",
                "stats": {
                    "count": cloud_buckets
                }
            })

        # Insight 7: Exposed Sensitive Files
        sensitive_files = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.security_files.has_issues": {"$eq": True}
        })
        
        if sensitive_files > 0:
            insights.append({
                "type": "critical",
                "title": "Exposed Sensitive Files",
                "message": f"{sensitive_files} asset(s) have exposed sensitive files (config files, credentials, etc.). This is a critical security risk.",
                "priority": "critical",
                "stats": {
                    "count": sensitive_files
                }
            })

        # Insight 8: Open Directories
        open_dirs = await assets_collection.count_documents({
            "user_id": uid,
            "misconfigurations.open_directories.has_issues": {"$eq": True}
        })
        
        if open_dirs > 0:
            insights.append({
                "type": "warning",
                "title": "Open Directory Listings",
                "message": f"{open_dirs} asset(s) have open directory listings enabled. This exposes file structure and can lead to information disclosure.",
                "priority": "medium",
                "stats": {
                    "count": open_dirs
                }
            })

        # Insight 10: Asset Growth Trend (renumbered)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: priority_order.get(x["priority"], 4))

        # Generate AI-powered recommendations for high-priority insights
        try:
            insights = await generate_batch_recommendations(insights)
        except Exception as e:
            logger.warning(f"Failed to generate LLM recommendations: {str(e)}")
            # Continue without recommendations if LLM fails

        return {"data": {"insights": insights}}

    except Exception as e:
        logger.error(f"Failed to get security insights: {str(e)}")
        return {"data": {"insights": []}}
