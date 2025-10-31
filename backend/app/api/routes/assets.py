"""
Asset Discovery and Management API Routes
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import Response
import csv
import io
from pydantic import BaseModel

from app.core.database import get_collection
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
    
    Runs scan directly as background task.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        users_collection = get_collection("users")
        scans_collection = get_collection("scans")

        # Get user to check plan and credits
        user_doc = await users_collection.find_one({"uid": uid})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        user_plan = user_doc.get("plan", "free")
        
        # Check scan credits (only for Free users)
        if user_plan == "free":
            credits_used = user_doc.get("scan_credits_used", 0)
            credits_limit = user_doc.get("scan_credits_limit", 10)

            if credits_used >= credits_limit:
                raise HTTPException(
                    status_code=402,
                    detail=f"Manual scan limit reached ({credits_limit} scans). Upgrade to Pro for unlimited manual scans and continuous monitoring."
                )
        # Pro users have unlimited manual scans

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

        # Increment scan credits used (only for Free users)
        if user_plan == "free":
            await users_collection.update_one(
                {"uid": uid},
                {"$inc": {"scan_credits_used": 1}}
            )

        # Run scan directly as background task
        import asyncio
        from app.tasks.scan_worker import _execute_scan_async
        
        # Create background task to run scan
        asyncio.create_task(_execute_scan_async(scan_id, scan_request.domain, uid))
        logger.info(f"Started scan job: {scan_id} for {scan_request.domain}")

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


@router.get("/export")
async def export_assets(
    request: Request,
    format: str = Query("csv", regex="^(csv|pdf)$"),
):
    """
    Export discovered assets, security misconfigurations, and data breaches.

    - csv: returns a CSV file
    - pdf: returns a formatted PDF summary with SME-friendly terms
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        # Fetch all assets for the user
        assets = await assets_collection.find({"user_id": uid}).sort("risk_score", -1).to_list(length=None)
        for asset in assets:
            asset.pop("_id", None)

        if format == "csv":
            output_text = io.StringIO()
            writer = csv.writer(output_text)

            # CSV header
            writer.writerow([
                "Asset",
                "Type",
                "Risk Score",
                "Risk Level",
                "HTTP Status",
                "Last Scanned",
                "Missing Headers Count",
                "SSL Issues Count",
                "DNS Issues Count",
                "Cloud Buckets Exposed",
                "Sensitive Files Exposed",
                "Open Directories",
                "Breach History Count"
            ])

            for a in assets:
                misc = a.get("misconfigurations", {}) or {}
                writer.writerow([
                    a.get("asset_value", ""),
                    a.get("asset_type", ""),
                    a.get("risk_score", 0),
                    a.get("risk_level", ""),
                    a.get("http_status", ""),
                    str(a.get("last_scanned_at", "") or ""),
                    len((misc.get("web_headers", {}) or {}).get("missing_headers", []) or []),
                    len((misc.get("ssl", {}) or {}).get("issues", []) or []),
                    len((misc.get("dns", {}) or {}).get("issues", []) or []),
                    len((misc.get("cloud_buckets", {}) or {}).get("buckets", []) or []),
                    len((misc.get("security_files", {}) or {}).get("sensitive_exposed", []) or []),
                    len((misc.get("open_directories", {}) or {}).get("open_directories", []) or []),
                    a.get("breach_history_count", 0),
                ])

            # Encode as UTF-8 with BOM for better Excel compatibility
            csv_bytes = ("\ufeff" + output_text.getvalue()).encode("utf-8")
            
            return Response(
                content=csv_bytes,
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": "attachment; filename=assets_export.csv"
                },
            )

        # PDF generation (using reportlab)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            logger.error("reportlab is not installed. Install with 'pip install reportlab'.")
            raise HTTPException(status_code=500, detail="PDF export requires reportlab. Please install it on the server.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("RECON-AI Summary Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Discovered Assets, Security Misconfigurations, and Data Breaches", styles["Heading2"]))
        story.append(Spacer(1, 12))

        # SME-friendly vulnerability terms section
        simple_terms = [
            ["Phishing", "Fake Message"],
            ["Smishing", "Fake SMS"],
            ["Vishing", "Fake Call"],
            ["Whaling", "Boss Scam"],
            ["Baiting", "Free Trap"],
            ["Malware", "Harmful File"],
            ["Ransomware", "Lock Attack"],
            ["Data Leak", "Info Spill"],
            ["Weak Passwords", "Easy Login"],
        ]

        story.append(Paragraph("Easy Terms (for SMEs)", styles["Heading3"]))
        terms_table = Table([["Technical", "Simple Term"]] + simple_terms, hAlign="LEFT")
        terms_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
        ]))
        story.append(terms_table)
        story.append(Spacer(1, 16))

        # Discovered Assets table (top 25 for brevity)
        story.append(Paragraph("Discovered Assets", styles["Heading3"]))
        asset_rows = [[
            "Asset", "Type", "Risk", "Level", "HTTP", "Last Scanned"
        ]]
        for a in assets[:25]:
            asset_rows.append([
                a.get("asset_value", ""),
                a.get("asset_type", ""),
                str(a.get("risk_score", 0)),
                a.get("risk_level", "").title(),
                str(a.get("http_status", "")),
                str(a.get("last_scanned_at", "")),
            ])
        assets_table = Table(asset_rows, hAlign="LEFT")
        assets_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(assets_table)
        story.append(Spacer(1, 16))

        # Security Misconfigurations summary
        story.append(Paragraph("Security Misconfigurations (Summary)", styles["Heading3"]))
        def count_total(items):
            return sum(items)

        missing_headers = [len((a.get("misconfigurations", {}) or {}).get("web_headers", {}).get("missing_headers", []) or []) for a in assets]
        ssl_issues = [len((a.get("misconfigurations", {}) or {}).get("ssl", {}).get("issues", []) or []) for a in assets]
        dns_issues = [len((a.get("misconfigurations", {}) or {}).get("dns", {}).get("issues", []) or []) for a in assets]
        bucket_exposed = [len((a.get("misconfigurations", {}) or {}).get("cloud_buckets", {}).get("buckets", []) or []) for a in assets]
        sensitive_files = [len((a.get("misconfigurations", {}) or {}).get("security_files", {}).get("sensitive_exposed", []) or []) for a in assets]
        open_dirs = [len((a.get("misconfigurations", {}) or {}).get("open_directories", {}).get("open_directories", []) or []) for a in assets]

        mis_rows = [
            ["Missing Security Headers", str(count_total(missing_headers))],
            ["SSL/TLS Issues", str(count_total(ssl_issues))],
            ["DNS Misconfigurations", str(count_total(dns_issues))],
            ["Exposed Cloud Storage", str(count_total(bucket_exposed))],
            ["Exposed Sensitive Files", str(count_total(sensitive_files))],
            ["Open Directory Listings", str(count_total(open_dirs))],
        ]
        mis_table = Table([["Category", "Total Issues"]] + mis_rows, hAlign="LEFT")
        mis_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
        ]))
        story.append(mis_table)
        story.append(Spacer(1, 16))

        # Data Breaches summary
        story.append(Paragraph("Data Breaches", styles["Heading3"]))
        total_breaches = sum([a.get("breach_history_count", 0) or 0 for a in assets])
        story.append(Paragraph(f"Total breaches detected across assets: <b>{total_breaches}</b>", styles["BodyText"]))

        # Build the PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=assets_report.pdf"
            },
        )

    except Exception as e:
        logger.error(f"Failed to export assets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export report")

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
