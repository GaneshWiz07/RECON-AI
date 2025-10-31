"""
Email Alert Service using SendGrid

Sends formatted email alerts for high and critical risk detections
"""

import os
import logging
from typing import Dict, List
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class EmailAlertService:
    """Service for sending security alert emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'alerts@reconai.com')
        self.enabled = bool(self.api_key and self.api_key != 'your_sendgrid_api_key')
        
        if not self.enabled:
            logger.warning("SendGrid not configured. Email alerts disabled.")
    
    async def send_risk_alert(
        self,
        to_email: str,
        asset_value: str,
        risk_score: int,
        risk_level: str,
        misconfigurations: Dict,
        scan_id: str
    ) -> bool:
        """
        Send email alert for high or critical risk detection
        
        Args:
            to_email: Recipient email address
            asset_value: The asset that triggered the alert
            risk_score: Risk score (0-100)
            risk_level: Risk level (high/critical)
            misconfigurations: Misconfiguration findings
            scan_id: Scan identifier
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email alerts disabled. Would have sent alert to {to_email}")
            return False
        
        try:
            # Generate email content
            subject = self._generate_subject(asset_value, risk_level, risk_score)
            html_content = self._generate_html_content(
                asset_value, risk_score, risk_level, misconfigurations, scan_id
            )
            
            # Create SendGrid message
            message = Mail(
                from_email=Email(self.from_email, 'RECON-AI Security Alerts'),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content('text/html', html_content)
            )
            
            # Send email
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Alert email sent to {to_email} for {asset_value} (Risk: {risk_level})")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
            return False
    
    def _generate_subject(self, asset_value: str, risk_level: str, risk_score: int) -> str:
        """Generate email subject line"""
        emoji = "🚨" if risk_level == "critical" else "⚠️"
        return f"{emoji} {risk_level.upper()} Risk Alert: {asset_value} (Score: {risk_score})"
    
    def _generate_html_content(
        self,
        asset_value: str,
        risk_score: int,
        risk_level: str,
        misconfigurations: Dict,
        scan_id: str
    ) -> str:
        """Generate formatted HTML email content"""
        
        # Determine colors based on risk level
        if risk_level == "critical":
            color = "#dc2626"  # red-600
            bg_color = "#fee2e2"  # red-50
        else:  # high
            color = "#ea580c"  # orange-600
            bg_color = "#ffedd5"  # orange-50
        
        # Build issue summary
        issues_html = self._build_issues_html(misconfigurations, color)
        
        # Generate timestamp
        timestamp = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            margin: 0;
            padding: 0;
            background-color: #f9fafb;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .alert-badge {{
            display: inline-block;
            background-color: {color};
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 14px;
            margin-top: 10px;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .asset-info {{
            background-color: {bg_color};
            border-left: 4px solid {color};
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .asset-info h2 {{
            margin: 0 0 10px 0;
            color: {color};
            font-size: 20px;
        }}
        .risk-score {{
            font-size: 48px;
            font-weight: bold;
            color: {color};
            margin: 10px 0;
        }}
        .issues-section {{
            margin: 30px 0;
        }}
        .issues-section h3 {{
            color: #374151;
            font-size: 18px;
            margin-bottom: 15px;
        }}
        .issue-category {{
            background-color: #f3f4f6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 3px solid {color};
        }}
        .issue-category h4 {{
            margin: 0 0 10px 0;
            color: #1f2937;
            font-size: 16px;
        }}
        .issue-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .issue-list li {{
            padding: 5px 0;
            color: #4b5563;
        }}
        .issue-list li:before {{
            content: "• ";
            color: {color};
            font-weight: bold;
            margin-right: 8px;
        }}
        .recommendations {{
            background-color: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .recommendations h3 {{
            color: #1e40af;
            margin: 0 0 15px 0;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin: 8px 0;
            color: #1e3a8a;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            background-color: #3b82f6;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .timestamp {{
            color: #6b7280;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ RECON-AI Security Alert</h1>
            <div class="alert-badge">{risk_level.upper()} RISK DETECTED</div>
        </div>
        
        <div class="content">
            <div class="asset-info">
                <h2>Asset Detected</h2>
                <p style="margin: 5px 0; font-size: 18px; font-family: monospace;">{asset_value}</p>
                <p style="margin: 10px 0 5px 0; color: #6b7280;">Risk Score</p>
                <div class="risk-score">{risk_score}/100</div>
            </div>
            
            <div class="issues-section">
                <h3>🔍 Security Issues Detected</h3>
                {issues_html}
            </div>
            
            <div class="recommendations">
                <h3>🔒 Immediate Actions Required</h3>
                <ul>
                    <li><strong>Review and fix all critical vulnerabilities immediately</strong></li>
                    <li>Implement missing security headers (CSP, HSTS, X-Frame-Options)</li>
                    <li>Renew or replace expired/weak SSL certificates</li>
                    <li>Remove or restrict access to exposed sensitive files</li>
                    <li>Configure proper cloud storage permissions</li>
                    <li>Fix DNS misconfigurations and dangling CNAMEs</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="https://your-recon-ai-domain.com/assets" class="button">View Full Details →</a>
            </div>
            
            <div class="timestamp">
                <strong>Scan ID:</strong> {scan_id}<br>
                <strong>Detected:</strong> {timestamp}
            </div>
        </div>
        
        <div class="footer">
            <p>This is an automated security alert from RECON-AI.<br>
            You're receiving this because critical security issues were detected on your assets.</p>
            <p style="margin-top: 20px;">
                <a href="https://your-recon-ai-domain.com" style="color: #3b82f6;">RECON-AI Dashboard</a> | 
                <a href="mailto:support@reconai.com" style="color: #3b82f6;">Contact Support</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _build_issues_html(self, misconfigurations: Dict, color: str) -> str:
        """Build HTML for issues section"""
        issues_html = ""
        
        # Web Headers
        if misconfigurations.get('web_headers', {}).get('has_issues'):
            headers = misconfigurations['web_headers']
            missing = headers.get('missing_headers', [])
            if missing:
                issues_html += f"""
                <div class="issue-category">
                    <h4>🌐 HTTP Security Headers ({len(missing)} missing)</h4>
                    <ul class="issue-list">
"""
                for header in missing[:5]:  # Show first 5
                    issues_html += f"<li>{header['header']} - {header['description']}</li>"
                if len(missing) > 5:
                    issues_html += f"<li>+{len(missing) - 5} more headers missing</li>"
                issues_html += "</ul></div>"
        
        # SSL/TLS
        if misconfigurations.get('ssl', {}).get('has_issues'):
            ssl_issues = misconfigurations['ssl'].get('issues', [])
            if ssl_issues:
                issues_html += f"""
                <div class="issue-category">
                    <h4>🔐 SSL/TLS Issues ({len(ssl_issues)})</h4>
                    <ul class="issue-list">
"""
                for issue in ssl_issues[:5]:
                    issues_html += f"<li>{issue.get('description', issue.get('type', 'Unknown issue'))}</li>"
                issues_html += "</ul></div>"
        
        # DNS
        if misconfigurations.get('dns', {}).get('has_issues'):
            dns_issues = misconfigurations['dns'].get('issues', [])
            if dns_issues:
                issues_html += f"""
                <div class="issue-category">
                    <h4>🌍 DNS Misconfigurations ({len(dns_issues)})</h4>
                    <ul class="issue-list">
"""
                for issue in dns_issues[:5]:
                    issues_html += f"<li>{issue.get('description', issue.get('type', 'Unknown issue'))}</li>"
                issues_html += "</ul></div>"
        
        # Cloud Buckets
        if misconfigurations.get('cloud_buckets', {}).get('has_issues'):
            buckets = misconfigurations['cloud_buckets'].get('buckets', [])
            if buckets:
                issues_html += f"""
                <div class="issue-category">
                    <h4>☁️ Exposed Cloud Storage ({len(buckets)})</h4>
                    <ul class="issue-list">
"""
                for bucket in buckets[:5]:
                    issues_html += f"<li>{bucket.get('description', 'Cloud bucket exposed')}</li>"
                issues_html += "</ul></div>"
        
        # Security Files
        if misconfigurations.get('security_files', {}).get('has_issues'):
            files = misconfigurations['security_files'].get('sensitive_exposed', [])
            if files:
                issues_html += f"""
                <div class="issue-category">
                    <h4>📁 Exposed Sensitive Files ({len(files)})</h4>
                    <ul class="issue-list">
"""
                for file in files[:5]:
                    issues_html += f"<li>{file.get('path', 'Sensitive file')} - {file.get('description', '')}</li>"
                issues_html += "</ul></div>"
        
        # Open Directories
        if misconfigurations.get('open_directories', {}).get('has_issues'):
            dirs = misconfigurations['open_directories'].get('open_directories', [])
            if dirs:
                issues_html += f"""
                <div class="issue-category">
                    <h4>📂 Open Directory Listings ({len(dirs)})</h4>
                    <ul class="issue-list">
"""
                for directory in dirs[:5]:
                    issues_html += f"<li>{directory.get('path', 'Directory')} - {directory.get('files_count', 0)} files exposed</li>"
                issues_html += "</ul></div>"
        
        if not issues_html:
            issues_html = "<p>No detailed issue information available.</p>"
        
        return issues_html


# Global instance
email_service = EmailAlertService()

