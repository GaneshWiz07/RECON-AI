"""
ML Model Prediction Module

Load trained model and make risk predictions on assets.
"""

import os
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)

# Global model and scaler (loaded once)
_model = None
_scaler = None


def load_model():
    """Load trained model and scaler from disk."""
    global _model, _scaler
    
    if _model is not None and _scaler is not None:
        return _model, _scaler
    
    try:
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        model_path = os.path.join(models_dir, "risk_model.joblib")
        scaler_path = os.path.join(models_dir, "scaler.joblib")
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            logger.warning("ML model files not found. Run 'python -m app.ml.train_model' to train model.")
            return None, None
        
        _model = joblib.load(model_path)
        _scaler = joblib.load(scaler_path)
        
        logger.info("ML model loaded successfully")
        return _model, _scaler
        
    except Exception as e:
        logger.error(f"Failed to load ML model: {str(e)}")
        return None, None


def extract_features(asset: dict) -> dict:
    """
    Extract features from asset data for ML prediction.
    
    Args:
        asset: Asset data dictionary
    
    Returns:
        Dictionary of features
    """
    open_ports = asset.get("open_ports", [])
    
    features = {
        "open_ports_count": len(open_ports),
        "has_ssh_open": 1 if 22 in open_ports else 0,
        "has_rdp_open": 1 if 3389 in open_ports else 0,
        "has_database_ports_open": 1 if any(p in [3306, 5432, 27017, 6379] for p in open_ports) else 0,
        "ssl_days_until_expiry": asset.get("ssl_days_until_expiry", 365),  # Default to valid
        "ssl_cert_is_self_signed": 0 if asset.get("ssl_cert_valid", True) else 1,
        "outdated_software_count": asset.get("outdated_software_count", 0),
        "has_default_credentials": 0,  # Would need specific detection
        "breach_history_count": asset.get("breach_history_count", 0),
        "http_security_headers_score": asset.get("http_security_headers_score", 0),
        "exposure_type_score": _calculate_exposure_score(asset),
    }
    
    return features


def _calculate_exposure_score(asset: dict) -> int:
    """
    Calculate exposure score based on asset type and properties.
    
    Args:
        asset: Asset data
    
    Returns:
        Exposure score 1-5
    """
    score = 1
    
    # More open ports = more exposure
    if len(asset.get("open_ports", [])) > 10:
        score += 2
    elif len(asset.get("open_ports", [])) > 5:
        score += 1
    
    # HTTP status indicates active service
    if asset.get("http_status") in [200, 301, 302]:
        score += 1
    
    # Public DNS records
    if asset.get("dns_records"):
        score += 1
    
    return min(score, 5)


def predict_risk_score(asset: dict) -> tuple:
    """
    Predict risk score using ML model.
    
    Args:
        asset: Asset data dictionary
    
    Returns:
        Tuple of (risk_score, risk_class)
        If model not available, returns None, None
    """
    model, scaler = load_model()
    
    if model is None or scaler is None:
        return None, None
    
    try:
        # Extract features
        features = extract_features(asset)
        
        # Convert to array in correct order
        feature_order = [
            "open_ports_count",
            "has_ssh_open",
            "has_rdp_open",
            "has_database_ports_open",
            "ssl_days_until_expiry",
            "ssl_cert_is_self_signed",
            "outdated_software_count",
            "has_default_credentials",
            "breach_history_count",
            "http_security_headers_score",
            "exposure_type_score",
        ]
        
        X = np.array([[features[f] for f in feature_order]])
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Predict risk class (0=low, 1=medium, 2=high, 3=critical)
        risk_class = model.predict(X_scaled)[0]
        
        # Get probability scores
        probabilities = model.predict_proba(X_scaled)[0]
        
        # Convert class to risk score (0-100)
        # Map classes to score ranges
        if risk_class == 0:  # low
            risk_score = int(probabilities[0] * 30)  # 0-30
        elif risk_class == 1:  # medium
            risk_score = int(30 + probabilities[1] * 30)  # 31-60
        elif risk_class == 2:  # high
            risk_score = int(60 + probabilities[2] * 25)  # 61-85
        else:  # critical
            risk_score = int(85 + probabilities[3] * 15)  # 86-100
        
        return risk_score, risk_class
        
    except Exception as e:
        logger.error(f"Failed to predict risk score: {str(e)}")
        return None, None


def get_risk_level(score: int) -> str:
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

