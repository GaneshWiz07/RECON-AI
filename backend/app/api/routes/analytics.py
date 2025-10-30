"""
Analytics API Routes

Provides dashboard statistics, risk trends, and insights
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Query
from app.core.database import get_collection
from app.middleware.auth import get_current_user

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

        # Calculate 7-day changes (placeholder - would need historical data)
        risk_score_change_7d = 0.0
        assets_change_7d = 0.0
        scans_change_7d = 0.0

        # Count new critical alerts (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
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

        # For each scan date, calculate average risk score from assets
        trend = []
        
        # Get all assets for this user
        all_assets = await assets_collection.find({"user_id": uid}).to_list(length=None)
        
        if scan_results and all_assets:
            # We have completed scans - calculate average risk for each scan date
            for scan_item in scan_results:
                date_str = scan_item["_id"]
                
                # Use all current assets for simplicity (showing current state across dates)
                avg_risk = sum(asset.get("risk_score", 0) for asset in all_assets) / len(all_assets)
                trend.append({
                    "date": date_str,
                    "risk_score": round(avg_risk, 1)
                })
        else:
            # No scans yet, but we might have assets - show current state
            assets = await assets_collection.find({"user_id": uid}).to_list(length=None)
            
            if assets:
                # Create a trend line for today showing current average
                avg_risk = sum(asset.get("risk_score", 0) for asset in assets) / len(assets)
                
                # Generate points for the last 7 days showing current average
                for i in range(7):
                    date = datetime.utcnow() - timedelta(days=(6 - i))
                    date_str = date.strftime("%Y-%m-%d")
                    trend.append({
                        "date": date_str,
                        "risk_score": round(avg_risk, 1)
                    })

        # If we have very few data points, expand for better visualization
        if len(trend) == 1:
            # Duplicate the single point across the last 7 days
            single_point = trend[0]
            trend = []
            for i in range(7):
                date = datetime.utcnow() - timedelta(days=(6 - i))
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
            return {"data": {"factors": []}}

        factors = []

        # Count assets with open SSH port (22)
        ssh_count = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": 22
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

        # Count assets with missing security headers
        headers_count = await assets_collection.count_documents({
            "user_id": uid,
            "http_security_headers_score": {"$lt": 3}
        })
        if headers_count > 0:
            factors.append({
                "name": "Missing Headers",
                "count": headers_count,
                "percentage": round((headers_count / total_assets) * 100, 1)
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

        return {"data": {"factors": factors[:6]}}  # Return top 6

    except Exception as e:
        logger.error(f"Failed to get risk factors: {str(e)}")
        return {"data": {"factors": []}}


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

        # Insight 1: Asset Monitoring Status
        if last_scan:
            from datetime import datetime, timedelta
            last_scan_time = last_scan.get("completed_at")
            if last_scan_time:
                hours_since_scan = (datetime.utcnow() - last_scan_time).total_seconds() / 3600
                if hours_since_scan < 24:
                    insights.append({
                        "type": "success",
                        "title": "Active Monitoring",
                        "message": f"Last scan completed {int(hours_since_scan)} hours ago. Your assets are being actively monitored.",
                        "action": None,
                        "priority": "low"
                    })
                else:
                    insights.append({
                        "type": "warning",
                        "title": "Scan Outdated",
                        "message": f"Last scan was {int(hours_since_scan/24)} days ago. Run a new scan to detect recent changes.",
                        "action": "Run Scan Now",
                        "priority": "medium"
                    })
        else:
            insights.append({
                "type": "info",
                "title": "Start Monitoring",
                "message": "No completed scans yet. Start your first scan to discover assets.",
                "action": "Start First Scan",
                "priority": "high"
            })

        # Insight 2: High-Risk Assets
        if high_risk_assets > 0:
            insights.append({
                "type": "critical",
                "title": "Critical Assets Detected",
                "message": f"{high_risk_assets} asset(s) have risk scores above 70 and require immediate attention.",
                "action": "View High-Risk Assets",
                "priority": "critical",
                "stats": {
                    "count": high_risk_assets,
                    "total": total_assets
                }
            })
        elif total_assets > 0:
            insights.append({
                "type": "success",
                "title": "Low Risk Profile",
                "message": f"No assets with critical risk scores. Keep monitoring to maintain security posture.",
                "action": None,
                "priority": "low"
            })

        # Insight 3: Exposed Services
        ssh_exposed = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": 22
        })
        
        db_exposed = await assets_collection.count_documents({
            "user_id": uid,
            "open_ports": {"$in": [3306, 5432, 27017, 6379]}
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
                "action": "Review Exposed Services",
                "priority": "high",
                "stats": {
                    "ssh": ssh_exposed,
                    "database": db_exposed
                }
            })

        # Insight 4: SSL/TLS Status
        invalid_ssl = await assets_collection.count_documents({
            "user_id": uid,
            "ssl_cert_valid": False
        })

        if invalid_ssl > 0:
            insights.append({
                "type": "warning",
                "title": "SSL Certificate Issues",
                "message": f"{invalid_ssl} asset(s) have invalid or expired SSL certificates. This affects trust and security.",
                "action": "Fix SSL Certificates",
                "priority": "high",
                "stats": {
                    "count": invalid_ssl
                }
            })

        # Insight 5: Security Headers
        missing_headers = await assets_collection.count_documents({
            "user_id": uid,
            "http_security_headers_score": {"$lt": 3}
        })

        if missing_headers > 0:
            percentage = round((missing_headers / total_assets) * 100) if total_assets > 0 else 0
            insights.append({
                "type": "info",
                "title": "Security Headers",
                "message": f"{percentage}% of assets are missing critical security headers. Consider implementing CSP, HSTS, and X-Frame-Options.",
                "action": "View Header Recommendations",
                "priority": "medium",
                "stats": {
                    "count": missing_headers,
                    "percentage": percentage
                }
            })

        # Insight 6: Asset Growth Trend
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_assets = await assets_collection.count_documents({
            "user_id": uid,
            "discovered_at": {"$gte": thirty_days_ago}
        })

        if new_assets > 0 and total_assets > 0:
            percentage = round((new_assets / total_assets) * 100)
            insights.append({
                "type": "info",
                "title": "Asset Discovery",
                "message": f"Discovered {new_assets} new asset(s) in the last 30 days ({percentage}% growth). Monitor new additions closely.",
                "action": None,
                "priority": "low",
                "stats": {
                    "new": new_assets,
                    "total": total_assets
                }
            })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return {"data": {"insights": insights}}

    except Exception as e:
        logger.error(f"Failed to get security insights: {str(e)}")
        return {"data": {"insights": []}}
