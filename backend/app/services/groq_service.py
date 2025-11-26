"""
Groq LLM Service for Security Recommendations

Provides AI-powered next step suggestions for security issues using Groq API.
"""

import os
import logging
from typing import Dict, Optional, List
from groq import Groq

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client: Optional[Groq] = None


def initialize_groq() -> None:
    """Initialize Groq client with API key from environment."""
    global groq_client
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.warning("GROQ_API_KEY not found in environment. LLM recommendations will be disabled.")
        groq_client = None
        return
    
    try:
        groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        groq_client = None


async def generate_security_recommendations(
    insight_type: str,
    title: str,
    message: str,
    stats: Optional[Dict] = None,
    asset_details: Optional[List[Dict]] = None
) -> Optional[str]:
    """
    Generate AI-powered security recommendations using Groq LLM.
    
    Args:
        insight_type: Type of security insight (critical, warning, info, etc.)
        title: Title of the security issue
        message: Description of the security issue
        stats: Optional statistics about the issue
        asset_details: Optional list of affected assets
    
    Returns:
        AI-generated recommendation string or None if generation fails
    """
    if not groq_client:
        return None
    
    try:
        # Build context for the LLM
        context_parts = [
            f"Security Issue: {title}",
            f"Description: {message}",
            f"Severity: {insight_type.upper()}"
        ]
        
        if stats:
            stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items()])
            context_parts.append(f"Statistics: {stats_str}")
        
        if asset_details:
            asset_count = len(asset_details)
            context_parts.append(f"Affected Assets: {asset_count} asset(s)")
            # Include sample asset names if available
            sample_assets = [a.get("asset_value", "") for a in asset_details[:3]]
            if sample_assets:
                context_parts.append(f"Sample Assets: {', '.join(sample_assets)}")
        
        context = "\n".join(context_parts)
        
        # Create prompt for the LLM
        prompt = f"""You are a cybersecurity expert providing actionable recommendations for security issues.

Context:
{context}

Provide a concise, actionable recommendation (2-3 sentences) for addressing this security issue. Focus on:
1. Immediate steps to mitigate the risk
2. Best practices for prevention
3. Specific technical actions if applicable

Be practical and specific. Do not include generic advice. Format as plain text without markdown."""

        # Call Groq API
        # Try different models in order of preference
        # Note: llama-3.1-70b-versatile has been decommissioned, using working alternatives
        models = [
            "llama-3.1-8b-instant",     # Fast and reliable (confirmed working)
            "mixtral-8x7b-32768",       # Alternative fallback
            "llama-3.1-70b-versatile"   # Deprecated, will skip automatically
        ]
        
        chat_completion = None
        last_error = None
        
        for model in models:
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cybersecurity expert specializing in infrastructure security, web application security, and cloud security. Provide practical, actionable recommendations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=200,
                    top_p=0.9
                )
                break  # Success, exit loop
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to use model {model}: {str(e)}")
                continue
        
        if not chat_completion:
            raise Exception(f"All models failed. Last error: {str(last_error)}")
        
        recommendation = chat_completion.choices[0].message.content.strip()
        logger.info(f"Generated recommendation for {title}")
        return recommendation
        
    except Exception as e:
        logger.error(f"Failed to generate recommendation: {str(e)}")
        return None


async def generate_batch_recommendations(
    insights: List[Dict]
) -> List[Dict]:
    """
    Generate recommendations for multiple insights in batch.
    
    Args:
        insights: List of insight dictionaries
    
    Returns:
        List of insights with added 'recommendation' field
    """
    if not groq_client:
        return insights
    
    # Generate recommendations for each insight
    for insight in insights:
        if insight.get("priority") in ["critical", "high"]:  # Only for high-priority issues
            recommendation = await generate_security_recommendations(
                insight_type=insight.get("type", "info"),
                title=insight.get("title", ""),
                message=insight.get("message", ""),
                stats=insight.get("stats"),
                asset_details=None  # Could be enhanced to pass asset details
            )
            
            if recommendation:
                insight["recommendation"] = recommendation
    
    return insights


async def generate_misconfiguration_recommendations(
    misconfigurations: Dict,
    asset_value: str
) -> Optional[str]:
    """
    Generate AI-powered recommendations for security misconfigurations.
    
    Args:
        misconfigurations: Dictionary containing misconfiguration findings
        asset_value: The asset URL/domain being analyzed
    
    Returns:
        AI-generated recommendation string or None if generation fails
    """
    if not groq_client:
        return None
    
    try:
        # Build detailed context from misconfigurations
        context_parts = [
            f"Asset: {asset_value}",
            f"Total Issues Found: {misconfigurations.get('total_issues', 0)}",
            f"Overall Severity: {misconfigurations.get('severity', 'unknown').upper()}"
        ]
        
        # Add specific issue details
        issues_found = []
        
        if misconfigurations.get('web_headers', {}).get('has_issues'):
            missing = misconfigurations['web_headers'].get('missing_headers', [])
            if missing:
                headers_list = [h.get('header', h) if isinstance(h, dict) else h for h in missing[:5]]
                issues_found.append(f"Missing Security Headers: {', '.join(headers_list)}")
        
        if misconfigurations.get('ssl', {}).get('has_issues'):
            ssl_issues = misconfigurations['ssl'].get('issues', [])
            if ssl_issues:
                issue_types = [issue.get('type', 'unknown').replace('_', ' ') for issue in ssl_issues[:3]]
                issues_found.append(f"SSL/TLS Issues: {', '.join(issue_types)}")
        
        if misconfigurations.get('dns', {}).get('has_issues'):
            dns_issues = misconfigurations['dns'].get('issues', [])
            if dns_issues:
                dns_types = [issue.get('type', 'unknown').replace('_', ' ') for issue in dns_issues[:3]]
                issues_found.append(f"DNS Misconfigurations: {', '.join(dns_types)}")
        
        if misconfigurations.get('cloud_buckets', {}).get('has_issues'):
            buckets = misconfigurations['cloud_buckets'].get('buckets', [])
            if buckets:
                bucket_count = len(buckets)
                issues_found.append(f"Exposed Cloud Storage Buckets: {bucket_count} bucket(s) found")
        
        if misconfigurations.get('security_files', {}).get('has_issues'):
            files = misconfigurations['security_files'].get('sensitive_exposed', [])
            if files:
                file_count = len(files)
                issues_found.append(f"Sensitive Files Exposed: {file_count} file(s) accessible")
        
        if misconfigurations.get('open_directories', {}).get('has_issues'):
            dirs = misconfigurations['open_directories'].get('open_directories', [])
            if dirs:
                dir_count = len(dirs)
                issues_found.append(f"Open Directories: {dir_count} directory listing(s) exposed")
        
        if issues_found:
            context_parts.append("\nSpecific Issues:")
            context_parts.extend([f"- {issue}" for issue in issues_found])
        else:
            # If no specific issues found, still provide context
            context_parts.append("\nNote: General security assessment requested.")
        
        context = "\n".join(context_parts)
        
        # Ensure we have enough context to generate a recommendation
        if len(context.strip()) < 50:
            logger.warning(f"Insufficient context for recommendation generation: {context}")
            return None
        
        # Create prompt for the LLM
        prompt = f"""You are a cybersecurity expert providing actionable recommendations for security misconfigurations.

Context:
{context}

Provide a comprehensive, actionable recommendation (3-4 sentences) for addressing these security misconfigurations. Focus on:
1. Immediate priority actions to fix the most critical issues
2. Step-by-step remediation guidance for each issue type
3. Best practices to prevent future misconfigurations
4. Specific technical implementation steps where applicable

Be practical, specific, and prioritize based on severity. Format as plain text without markdown."""
        
        # Call Groq API
        # Note: llama-3.1-70b-versatile has been decommissioned, using working alternatives
        models = [
            "llama-3.1-8b-instant",     # Fast and reliable (confirmed working)
            "mixtral-8x7b-32768",       # Alternative fallback
            "llama-3.1-70b-versatile"   # Deprecated, will skip automatically
        ]
        
        chat_completion = None
        last_error = None
        
        for model in models:
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cybersecurity expert specializing in infrastructure security, web application security, cloud security, and security misconfigurations. Provide practical, actionable, step-by-step recommendations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=300,
                    top_p=0.9
                )
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to use model {model}: {str(e)}")
                continue
        
        if not chat_completion:
            raise Exception(f"All models failed. Last error: {str(last_error)}")
        
        recommendation = chat_completion.choices[0].message.content.strip()
        
        if not recommendation or len(recommendation) == 0:
            logger.warning(f"Generated empty recommendation for {asset_value}")
            return None
        
        logger.info(f"Generated misconfiguration recommendation for {asset_value}: {recommendation[:100]}...")
        return recommendation
        
    except Exception as e:
        logger.error(f"Failed to generate misconfiguration recommendation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def generate_summary_report_recommendations(
    assets: List[Dict]
) -> Optional[str]:
    """
    Generate AI-powered recommendations for the overall security summary report.
    
    Args:
        assets: List of asset dictionaries with their security findings
    
    Returns:
        AI-generated recommendation string or None if generation fails
    """
    if not groq_client:
        return None
    
    try:
        # Calculate summary statistics
        total_assets = len(assets)
        high_risk = len([a for a in assets if a.get('risk_level') in ['high', 'critical']])
        medium_risk = len([a for a in assets if a.get('risk_level') == 'medium'])
        
        # Count misconfigurations
        missing_headers = sum([len((a.get('misconfigurations', {}).get('web_headers', {})).get('missing_headers', [])) for a in assets])
        ssl_issues = sum([len((a.get('misconfigurations', {}).get('ssl', {})).get('issues', [])) for a in assets])
        dns_issues = sum([len((a.get('misconfigurations', {}).get('dns', {})).get('issues', [])) for a in assets])
        exposed_buckets = sum([len((a.get('misconfigurations', {}).get('cloud_buckets', {})).get('buckets', [])) for a in assets])
        exposed_files = sum([len((a.get('misconfigurations', {}).get('security_files', {})).get('sensitive_exposed', [])) for a in assets])
        open_dirs = sum([len((a.get('misconfigurations', {}).get('open_directories', {})).get('open_directories', [])) for a in assets])
        
        total_breaches = sum([a.get('breach_history_count', 0) for a in assets])
        
        # Build context
        context_parts = [
            f"Security Summary Report",
            f"Total Assets Scanned: {total_assets}",
            f"High/Critical Risk Assets: {high_risk}",
            f"Medium Risk Assets: {medium_risk}",
            "",
            "Security Issues Found:",
            f"- Missing Security Headers: {missing_headers}",
            f"- SSL/TLS Issues: {ssl_issues}",
            f"- DNS Misconfigurations: {dns_issues}",
            f"- Exposed Cloud Storage Buckets: {exposed_buckets}",
            f"- Sensitive Files Exposed: {exposed_files}",
            f"- Open Directories: {open_dirs}",
            f"- Total Data Breaches (Historical): {total_breaches}"
        ]
        
        context = "\n".join(context_parts)
        
        # Create prompt for the LLM
        prompt = f"""You are a cybersecurity expert providing strategic recommendations for an organization's security posture.

Context:
{context}

Provide a comprehensive, strategic recommendation (4-5 sentences) for improving the overall security posture. Focus on:
1. Priority actions based on the most critical issues found
2. Strategic approach to remediation (what to fix first)
3. Best practices for ongoing security monitoring
4. Recommendations for security hardening across all assets
5. Long-term security improvement strategies

Be strategic, prioritize based on risk, and provide actionable guidance. Format as plain text without markdown."""
        
        # Call Groq API
        # Note: llama-3.1-70b-versatile has been decommissioned, using working alternatives
        models = [
            "llama-3.1-8b-instant",     # Fast and reliable (confirmed working)
            "mixtral-8x7b-32768",       # Alternative fallback
            "llama-3.1-70b-versatile"   # Deprecated, will skip automatically
        ]
        
        chat_completion = None
        last_error = None
        
        for model in models:
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a Chief Information Security Officer (CISO) providing strategic security recommendations. Provide high-level, actionable guidance for improving organizational security posture."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=350,
                    top_p=0.9
                )
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to use model {model}: {str(e)}")
                continue
        
        if not chat_completion:
            raise Exception(f"All models failed. Last error: {str(last_error)}")
        
        recommendation = chat_completion.choices[0].message.content.strip()
        logger.info("Generated summary report recommendation")
        return recommendation
        
    except Exception as e:
        logger.error(f"Failed to generate summary report recommendation: {str(e)}")
        return None


async def generate_security_terms(assets: List[Dict]) -> List[tuple]:
    """
    Generate relevant security terms in simple language based on scan results.
    
    Args:
        assets: List of asset dictionaries with their security findings
    
    Returns:
        List of tuples (technical_term, simple_explanation) or empty list if generation fails
    """
    if not groq_client:
        return []
    
    try:
        # Extract security issues found in the scan
        security_issues = []
        
        # Count misconfigurations
        missing_headers = sum([len((a.get('misconfigurations', {}).get('web_headers', {})).get('missing_headers', [])) for a in assets])
        ssl_issues = sum([len((a.get('misconfigurations', {}).get('ssl', {})).get('issues', [])) for a in assets])
        dns_issues = sum([len((a.get('misconfigurations', {}).get('dns', {})).get('issues', [])) for a in assets])
        exposed_buckets = sum([len((a.get('misconfigurations', {}).get('cloud_buckets', {})).get('buckets', [])) for a in assets])
        exposed_files = sum([len((a.get('misconfigurations', {}).get('security_files', {})).get('sensitive_exposed', [])) for a in assets])
        open_dirs = sum([len((a.get('misconfigurations', {}).get('open_directories', {})).get('open_directories', [])) for a in assets])
        total_breaches = sum([a.get('breach_history_count', 0) for a in assets])
        high_risk_assets = len([a for a in assets if a.get('risk_level') in ['high', 'critical']])
        
        # Build context of what was found
        context_parts = [
            f"Security Scan Results:",
            f"- Missing Security Headers: {missing_headers}",
            f"- SSL/TLS Issues: {ssl_issues}",
            f"- DNS Misconfigurations: {dns_issues}",
            f"- Exposed Cloud Storage: {exposed_buckets}",
            f"- Sensitive Files Exposed: {exposed_files}",
            f"- Open Directories: {open_dirs}",
            f"- Historical Data Breaches: {total_breaches}",
            f"- High/Critical Risk Assets: {high_risk_assets}"
        ]
        
        # Get specific issue types found
        issue_types = []
        for asset in assets[:10]:  # Sample first 10 assets
            misc = asset.get('misconfigurations', {})
            if misc.get('web_headers', {}).get('has_issues'):
                issue_types.append('Missing Security Headers')
            if misc.get('ssl', {}).get('has_issues'):
                issue_types.append('SSL/TLS Certificate Issues')
            if misc.get('dns', {}).get('has_issues'):
                issue_types.append('DNS Configuration Problems')
            if misc.get('cloud_buckets', {}).get('has_issues'):
                issue_types.append('Exposed Cloud Storage')
            if misc.get('security_files', {}).get('has_issues'):
                issue_types.append('Sensitive File Exposure')
            if misc.get('open_directories', {}).get('has_issues'):
                issue_types.append('Open Directory Listings')
            if asset.get('breach_history_count', 0) > 0:
                issue_types.append('Data Breach History')
        
        unique_issues = list(set(issue_types))
        if unique_issues:
            context_parts.append(f"\nSpecific Issues Found: {', '.join(unique_issues[:5])}")
        
        context = "\n".join(context_parts)
        
        # Create prompt for the LLM
        prompt = f"""Based on the following security scan results, generate 6-9 relevant security terms in simple language that business owners would understand.

Scan Results:
{context}

For each security issue found, provide:
1. The technical term (e.g., "Phishing", "SSL Certificate", "Data Breach")
2. A simple, business-friendly explanation (e.g., "Fake Email", "Website Security Lock", "Hacked Database")

Format your response as a JSON array of arrays, where each inner array has exactly 2 elements: [technical_term, simple_explanation]

Example format:
[
  ["Phishing", "Fake Email"],
  ["SSL Certificate", "Website Security Lock"],
  ["Data Breach", "Hacked Database"]
]

Only include terms relevant to the issues found in the scan. Return ONLY valid JSON, no other text."""
        
        # Call Groq API
        models = [
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "llama-3.1-70b-versatile"
        ]
        
        chat_completion = None
        last_error = None
        
        for model in models:
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cybersecurity educator who explains technical security terms in simple, business-friendly language. Always respond with valid JSON arrays only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=400,
                    top_p=0.9
                )
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to use model {model} for terms generation: {str(e)}")
                continue
        
        if not chat_completion:
            logger.error(f"All models failed for terms generation. Last error: {str(last_error)}")
            return []
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        import json
        import re
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()
        
        try:
            terms_list = json.loads(response_text)
            if isinstance(terms_list, list) and len(terms_list) > 0:
                # Validate format
                valid_terms = []
                for term_pair in terms_list:
                    if isinstance(term_pair, list) and len(term_pair) == 2:
                        valid_terms.append((str(term_pair[0]), str(term_pair[1])))
                
                if valid_terms:
                    logger.info(f"Generated {len(valid_terms)} security terms")
                    return valid_terms
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {str(e)}")
            logger.error(f"Response text: {response_text}")
        
        # Fallback: return empty list
        return []
        
    except Exception as e:
        logger.error(f"Failed to generate security terms: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

