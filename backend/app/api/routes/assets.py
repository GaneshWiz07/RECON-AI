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
from app.services.groq_service import generate_misconfiguration_recommendations, generate_summary_report_recommendations, generate_security_terms

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


@router.get("/export-detailed-report")
async def export_detailed_security_report(request: Request):
    """
    Export a comprehensive detailed security report in PDF format.
    Includes executive summary, detailed findings, recommendations, and risk analysis.
    """
    user = get_current_user(request)
    uid = user["uid"]
    
    try:
        logger.info(f"Starting detailed PDF export for user {uid}")
        assets_collection = get_collection("assets")
        
        # Fetch all assets for the user
        assets = await assets_collection.find({"user_id": uid}).sort("risk_score", -1).to_list(length=None)
        logger.info(f"Found {len(assets)} assets for PDF export")
        
        for asset in assets:
            asset.pop("_id", None)
        
        if not assets:
            logger.warning("No assets found for PDF export")
            raise HTTPException(status_code=404, detail="No assets found to generate report")
        
        # PDF generation (using reportlab)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from datetime import datetime
            logger.info("ReportLab imports successful")
        except ImportError as e:
            logger.error(f"reportlab import failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF export requires reportlab. Error: {str(e)}")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=0.75*inch, 
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8,
            spaceBefore=8
        )
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("RECON-AI", title_style))
        story.append(Paragraph("Detailed Security Report", styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"Total Assets Scanned: <b>{len(assets)}</b>", styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        # Calculate statistics
        total_assets = len(assets)
        high_risk = len([a for a in assets if a.get('risk_level') in ['high', 'critical']])
        medium_risk = len([a for a in assets if a.get('risk_level') == 'medium'])
        low_risk = len([a for a in assets if a.get('risk_level') == 'low'])
        
        # Safely calculate misconfiguration counts
        def safe_get_list(asset, *keys, default=None):
            """Safely get nested list value"""
            if default is None:
                default = []
            value = asset
            for key in keys:
                if not isinstance(value, dict):
                    return default
                value = value.get(key)
                if value is None:
                    return default
            return value if isinstance(value, list) else default
        
        missing_headers = sum([len(safe_get_list(a, 'misconfigurations', 'web_headers', 'missing_headers')) for a in assets])
        ssl_issues = sum([len(safe_get_list(a, 'misconfigurations', 'ssl', 'issues')) for a in assets])
        dns_issues = sum([len(safe_get_list(a, 'misconfigurations', 'dns', 'issues')) for a in assets])
        exposed_buckets = sum([len(safe_get_list(a, 'misconfigurations', 'cloud_buckets', 'buckets')) for a in assets])
        exposed_files = sum([len(safe_get_list(a, 'misconfigurations', 'security_files', 'sensitive_exposed')) for a in assets])
        open_dirs = sum([len(safe_get_list(a, 'misconfigurations', 'open_directories', 'open_directories')) for a in assets])
        total_breaches = sum([a.get('breach_history_count', 0) or 0 for a in assets])
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Assets", str(total_assets)],
            ["High/Critical Risk Assets", str(high_risk)],
            ["Medium Risk Assets", str(medium_risk)],
            ["Low Risk Assets", str(low_risk)],
            ["Missing Security Headers", str(missing_headers)],
            ["SSL/TLS Issues", str(ssl_issues)],
            ["DNS Misconfigurations", str(dns_issues)],
            ["Exposed Cloud Storage", str(exposed_buckets)],
            ["Sensitive Files Exposed", str(exposed_files)],
            ["Open Directories", str(open_dirs)],
            ["Historical Data Breaches", str(total_breaches)],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f9fafb")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Risk Assessment
        story.append(Paragraph("Risk Assessment", heading_style))
        risk_text = f"""
        This security assessment identified <b>{total_assets}</b> assets with varying levels of risk. 
        <b>{high_risk}</b> assets require immediate attention due to high or critical risk scores. 
        The scan detected <b>{missing_headers + ssl_issues + dns_issues + exposed_buckets + exposed_files + open_dirs}</b> 
        total security misconfigurations across all assets.
        """
        story.append(Paragraph(risk_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Detailed Asset Findings
        story.append(PageBreak())
        story.append(Paragraph("Detailed Asset Findings", heading_style))
        
        # Group assets by risk level
        critical_assets = [a for a in assets if a.get('risk_level') == 'critical']
        high_assets = [a for a in assets if a.get('risk_level') == 'high']
        medium_assets = [a for a in assets if a.get('risk_level') == 'medium']
        
        for risk_level, asset_list, title in [
            ('critical', critical_assets, 'Critical Risk Assets'),
            ('high', high_assets, 'High Risk Assets'),
            ('medium', medium_assets, 'Medium Risk Assets')
        ]:
            if asset_list:
                story.append(Paragraph(title, subheading_style))
                
                asset_data = [["Asset", "Type", "Risk Score", "Issues", "Last Scanned"]]
                for asset in asset_list[:20]:  # Limit to top 20 per category
                    misc = asset.get('misconfigurations', {}) or {}
                    total_issues = misc.get('total_issues', 0)
                    last_scanned = asset.get('last_scanned_at')
                    if last_scanned:
                        if isinstance(last_scanned, str):
                            last_scanned_str = last_scanned[:10]
                        else:
                            # It's a datetime object
                            last_scanned_str = str(last_scanned)[:10]
                    else:
                        last_scanned_str = 'Never'
                    
                    asset_data.append([
                        asset.get('asset_value', 'N/A')[:40],
                        asset.get('asset_type', 'N/A'),
                        str(asset.get('risk_score', 0)),
                        str(total_issues),
                        last_scanned_str
                    ])
                
                asset_table = Table(asset_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 0.7*inch, 1*inch])
                asset_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f9fafb")),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                ]))
                story.append(asset_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Security Misconfigurations Detail
        story.append(PageBreak())
        story.append(Paragraph("Security Misconfigurations Detail", heading_style))
        
        misconfig_data = [
            ["Category", "Total Issues", "Affected Assets"]
        ]
        
        # Count affected assets for each category
        def safe_get_bool(asset, *keys, default=False):
            """Safely get nested boolean value"""
            value = asset
            for key in keys:
                if not isinstance(value, dict):
                    return default
                value = value.get(key)
                if value is None:
                    return default
            return bool(value) if value is not None else default
        
        headers_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'web_headers', 'has_issues')])
        ssl_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'ssl', 'has_issues')])
        dns_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'dns', 'has_issues')])
        buckets_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'cloud_buckets', 'has_issues')])
        files_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'security_files', 'has_issues')])
        dirs_affected = len([a for a in assets if safe_get_bool(a, 'misconfigurations', 'open_directories', 'has_issues')])
        
        misconfig_data.extend([
            ["Missing Security Headers", str(missing_headers), str(headers_affected)],
            ["SSL/TLS Certificate Issues", str(ssl_issues), str(ssl_affected)],
            ["DNS Misconfigurations", str(dns_issues), str(dns_affected)],
            ["Exposed Cloud Storage", str(exposed_buckets), str(buckets_affected)],
            ["Sensitive Files Exposed", str(exposed_files), str(files_affected)],
            ["Open Directory Listings", str(open_dirs), str(dirs_affected)],
        ])
        
        misconfig_table = Table(misconfig_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        misconfig_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f9fafb")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
        ]))
        story.append(misconfig_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Data Breach Information
        if total_breaches > 0:
            story.append(Paragraph("Data Breach History", subheading_style))
            breach_text = f"""
            <b>{len([a for a in assets if a.get('breach_history_count', 0) > 0])}</b> assets have been involved in 
            <b>{total_breaches}</b> known data breaches according to the Have I Been Pwned database. 
            It is recommended to review security practices and consider password rotation for affected accounts.
            """
            story.append(Paragraph(breach_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Recommendations Section
        story.append(PageBreak())
        story.append(Paragraph("Recommendations", heading_style))
        
        recommendations = []
        if missing_headers > 0:
            recommendations.append("Implement missing security headers (Content-Security-Policy, X-Frame-Options, etc.) to protect against common web attacks.")
        if ssl_issues > 0:
            recommendations.append("Review and renew SSL/TLS certificates. Ensure certificates are valid and not expired.")
        if dns_issues > 0:
            recommendations.append("Fix DNS misconfigurations to prevent potential DNS takeover attacks.")
        if exposed_buckets > 0:
            recommendations.append("Restrict access to cloud storage buckets. Ensure buckets are not publicly accessible unless necessary.")
        if exposed_files > 0:
            recommendations.append("Remove or restrict access to sensitive files (config files, backups, etc.) that are publicly accessible.")
        if open_dirs > 0:
            recommendations.append("Disable directory listings to prevent information disclosure.")
        if total_breaches > 0:
            recommendations.append("Review breach history and implement password rotation policies for affected accounts.")
        if high_risk > 0:
            recommendations.append("Prioritize remediation of high and critical risk assets immediately.")
        
        if not recommendations:
            recommendations.append("No critical security issues detected. Continue monitoring and maintain current security practices.")
        
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("This report was generated by RECON-AI Security Platform", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                            textColor=colors.grey, alignment=TA_CENTER)))
        
        # Build the PDF
        logger.info("Building PDF document...")
        try:
            doc.build(story)
            buffer.seek(0)  # Reset buffer position to beginning
            pdf_bytes = buffer.getvalue()
            buffer.close()
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
            
            # Validate PDF bytes
            if len(pdf_bytes) == 0:
                raise ValueError("Generated PDF is empty")
            if not pdf_bytes.startswith(b'%PDF'):
                raise ValueError("Generated file does not appear to be a valid PDF")
                
        except Exception as pdf_error:
            logger.error(f"Error building PDF: {str(pdf_error)}")
            import traceback
            logger.error(f"PDF build traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to build PDF: {str(pdf_error)}")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=detailed_security_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
                "Content-Length": str(len(pdf_bytes))
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate detailed security report: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate detailed report: {str(e)}")


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

@router.delete("/")
async def clear_all_assets(request: Request):
    """
    Clear all scanned records (assets) for the current user.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        assets_collection = get_collection("assets")

        # Delete all assets for this user
        result = await assets_collection.delete_many({"user_id": uid})
        
        logger.info(f"Cleared {result.deleted_count} assets for user {uid}")

        return {
            "data": {
                "deleted_count": result.deleted_count
            },
            "message": f"Successfully cleared {result.deleted_count} asset(s)"
        }

    except Exception as e:
        logger.error(f"Failed to clear assets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear assets")


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


class MisconfigurationRecommendationRequest(BaseModel):
    asset_id: str


class SummaryRecommendationRequest(BaseModel):
    domain: Optional[str] = None


@router.post("/misconfiguration-recommendation")
async def get_misconfiguration_recommendation(
    request: Request,
    recommendation_request: MisconfigurationRecommendationRequest
):
    """
    Generate AI-powered recommendations for a specific asset's misconfigurations.
    """
    user = get_current_user(request)
    
    try:
        assets_collection = get_collection("assets")
        
        # Try to find asset by asset_id first
        asset = await assets_collection.find_one({
            "asset_id": recommendation_request.asset_id,
            "user_id": user["uid"]
        })
        
        # If not found by asset_id, try finding by asset_value (for older assets without asset_id)
        if not asset:
            asset = await assets_collection.find_one({
                "asset_value": recommendation_request.asset_id,
                "user_id": user["uid"]
            })
        
        # If still not found, try _id if it looks like MongoDB ObjectId
        if not asset:
            try:
                from bson import ObjectId
                asset = await assets_collection.find_one({
                    "_id": ObjectId(recommendation_request.asset_id),
                    "user_id": user["uid"]
                })
            except Exception:
                pass
        
        if not asset:
            logger.warning(f"Asset not found: asset_id={recommendation_request.asset_id}, user_id={user['uid']}")
            raise HTTPException(status_code=404, detail=f"Asset not found with ID: {recommendation_request.asset_id}")
        
        misconfigurations = asset.get("misconfigurations", {})
        asset_value = asset.get("asset_value", "")
        
        # Log misconfigurations for debugging
        logger.info(f"Asset misconfigurations for {asset_value}: {misconfigurations}")
        logger.info(f"Total issues: {misconfigurations.get('total_issues', 0) if misconfigurations else 0}")
        
        if not misconfigurations or misconfigurations.get("total_issues", 0) == 0:
            logger.info(f"No misconfigurations found for asset {asset_value}")
            return {
                "data": {
                    "recommendation": "No security misconfigurations detected for this asset. Continue monitoring and maintain current security practices."
                }
            }
        
        # Generate AI recommendation
        logger.info(f"Generating recommendation for asset {asset_value} with {misconfigurations.get('total_issues', 0)} issues")
        try:
            recommendation = await generate_misconfiguration_recommendations(
                misconfigurations=misconfigurations,
                asset_value=asset_value
            )
            
            logger.info(f"Recommendation result: {recommendation[:100] if recommendation else 'None'}...")
            
            if not recommendation or not recommendation.strip():
                logger.warning(f"Empty recommendation returned for asset {asset_value}")
                return {
                    "data": {
                        "recommendation": "Unable to generate AI recommendations at this time. Please ensure GROQ_API_KEY is configured and check server logs for details."
                    }
                }
            
            return {
                "data": {
                    "recommendation": recommendation.strip()
                }
            }
        except Exception as e:
            logger.error(f"Exception generating recommendation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "data": {
                    "recommendation": f"Error generating recommendation: {str(e)}. Please check server logs for details."
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate misconfiguration recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")


@router.post("/summary-recommendation")
async def get_summary_recommendation(
    request: Request,
    recommendation_request: SummaryRecommendationRequest
):
    """
    Generate AI-powered recommendations for the overall security summary report.
    """
    user = get_current_user(request)
    
    try:
        assets_collection = get_collection("assets")
        
        # Build query
        query = {"user_id": user["uid"]}
        if recommendation_request.domain:
            query["domain"] = recommendation_request.domain
        
        # Get all assets for the user (or filtered by domain)
        assets_cursor = assets_collection.find(query)
        assets = await assets_cursor.to_list(length=1000)  # Limit to prevent memory issues
        
        if not assets:
            return {
                "data": {
                    "recommendation": "No assets found. Run a scan to generate security recommendations."
                }
            }
        
        # Remove MongoDB _id fields
        for asset in assets:
            asset.pop("_id", None)
        
        # Generate AI recommendation
        recommendation = await generate_summary_report_recommendations(assets=assets)
        
        if not recommendation:
            return {
                "data": {
                    "recommendation": "Unable to generate AI recommendations at this time. Please ensure GROQ_API_KEY is configured."
                }
            }
        
        return {
            "data": {
                "recommendation": recommendation
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate summary recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")


@router.post("/security-terms")
async def get_security_terms(
    request: Request,
    recommendation_request: SummaryRecommendationRequest
):
    """
    Generate AI-powered security terms in simple language based on scan results.
    """
    user = get_current_user(request)
    
    try:
        assets_collection = get_collection("assets")
        
        # Build query
        query = {"user_id": user["uid"]}
        if recommendation_request.domain:
            query["domain"] = recommendation_request.domain
        
        # Get all assets for the user (or filtered by domain)
        assets_cursor = assets_collection.find(query)
        assets = await assets_cursor.to_list(length=1000)  # Limit to prevent memory issues
        
        if not assets:
            return {
                "data": {
                    "terms": []
                }
            }
        
        # Remove MongoDB _id fields
        for asset in assets:
            asset.pop("_id", None)
        
        # Generate AI terms
        terms = await generate_security_terms(assets=assets)
        
        # Convert list of tuples to list of lists for JSON serialization
        terms_list = [[term[0], term[1]] for term in terms] if terms else []
        
        return {
            "data": {
                "terms": terms_list
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate security terms: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate security terms")
