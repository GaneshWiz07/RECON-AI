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
    Get risk score trend over time.

    Args:
        days: Number of days to retrieve (1-90)

    Returns:
        Daily risk score averages
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        scans_collection = get_collection("scans")

        # Get scans from last N days
        start_date = datetime.utcnow() - timedelta(days=days)

        pipeline = [
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
                    "avg_risk": {"$avg": "$risk_score"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        results = await scans_collection.aggregate(pipeline).to_list(length=days)

        trend = [
            {"date": item["_id"], "risk_score": int(item["avg_risk"])}
            for item in results
        ]

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
