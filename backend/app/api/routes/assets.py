"""
Asset Discovery and Management API Routes
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from app.core.database import get_collection
from app.core.redis_client import get_redis_queue
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assets", tags=["assets"])


# Request/Response models
class ScanRequest(BaseModel):
    domain: str
    scan_subdomains: bool = True


class ScanResponse(BaseModel):
    scan_id: str
    domain: str
    status: str
    estimated_completion: str


@router.post("/scan", response_model=dict, status_code=202)
async def start_asset_scan(request: Request, scan_request: ScanRequest):
    """
    Start new asset discovery scan for a domain.

    Checks user credits, creates scan record, and queues scan job.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        users_collection = get_collection("users")
        scans_collection = get_collection("scans")

        # Get user to check credits
        user_doc = await users_collection.find_one({"uid": uid})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Check scan credits
        credits_used = user_doc.get("scan_credits_used", 0)
        credits_limit = user_doc.get("scan_credits_limit", 10)

        if credits_used >= credits_limit:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient scan credits. Upgrade to Pro for more credits."
            )

        # Create scan record
        scan_id = f"scn_{datetime.utcnow().timestamp()}"
        scan_doc = {
            "scan_id": scan_id,
            "user_id": uid,
            "workspace_id": uid,
            "domain": scan_request.domain,
            "scan_type": "full",
            "scan_status": "pending",
            "scan_subdomains": scan_request.scan_subdomains,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
        }

        await scans_collection.insert_one(scan_doc)

        # Increment scan credits used
        await users_collection.update_one(
            {"uid": uid},
            {"$inc": {"scan_credits_used": 1}}
        )

        # Queue scan job in Redis
        try:
            queue = get_redis_queue()
            from app.tasks.scan_worker import execute_scan
            queue.enqueue(execute_scan, scan_id, scan_request.domain, uid)
            logger.info(f"Queued scan job: {scan_id} for {scan_request.domain}")
        except Exception as e:
            logger.error(f"Failed to queue scan job: {str(e)}")
            # Note: Scan record created but job not queued - could implement retry

        # Estimate completion time (2-5 minutes)
        estimated_completion = datetime.utcnow()
        estimated_completion = estimated_completion.replace(
            minute=estimated_completion.minute + 3
        )

        return {
            "data": {
                "scan_id": scan_id,
                "domain": scan_request.domain,
                "status": "pending",
                "estimated_completion": estimated_completion.isoformat()
            },
            "message": "Scan started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start scan")


@router.get("/")
async def list_assets(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("risk_score", regex="^(risk_score|discovered_at|asset_value)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    risk_level: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    asset_type: Optional[str] = Query(None, regex="^(domain|subdomain|ip_address)$"),
    search: Optional[str] = None
):
    """
    List all assets for current user with pagination and filtering.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        # Build query
        query = {"user_id": uid}

        if risk_level:
            query["risk_level"] = risk_level

        if asset_type:
            query["asset_type"] = asset_type

        if search:
            query["asset_value"] = {"$regex": search, "$options": "i"}

        # Count total
        total = await assets_collection.count_documents(query)

        # Sort
        sort_field = sort_by
        sort_direction = -1 if sort_order == "desc" else 1

        # Paginate
        skip = (page - 1) * limit
        cursor = assets_collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        assets = await cursor.to_list(length=limit)

        # Remove MongoDB _id
        for asset in assets:
            asset.pop("_id", None)

        return {
            "data": {
                "assets": assets,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to list assets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assets")


@router.get("/{asset_id}")
async def get_asset_details(request: Request, asset_id: str):
    """
    Get detailed information for a single asset.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        asset = await assets_collection.find_one({
            "asset_id": asset_id,
            "user_id": uid
        })

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset.pop("_id", None)

        return {"data": {"asset": asset}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset {asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve asset")
