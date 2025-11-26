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
        models = [
            "llama-3.1-70b-versatile",  # Fast and capable
            "llama-3.1-8b-instant",     # Faster fallback
            "mixtral-8x7b-32768"        # Alternative
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

