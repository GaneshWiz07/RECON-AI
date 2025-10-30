"""
ML Model Training Script

Generates synthetic training data and trains a Logistic Regression model
for risk scoring.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_samples=10000):
    """
    Generate synthetic training data for risk scoring.

    Features:
    - open_ports_count
    - has_ssh_open
    - has_rdp_open
    - has_database_ports_open
    - ssl_days_until_expiry
    - ssl_cert_is_self_signed
    - outdated_software_count
    - has_default_credentials
    - breach_history_count
    - http_security_headers_score
    - exposure_type_score

    Labels: risk_score (0-100)
    """
    logger.info(f"Generating {n_samples} synthetic samples...")

    np.random.seed(42)

    data = {
        "open_ports_count": np.random.randint(0, 20, n_samples),
        "has_ssh_open": np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        "has_rdp_open": np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        "has_database_ports_open": np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        "ssl_days_until_expiry": np.random.randint(-30, 365, n_samples),
        "ssl_cert_is_self_signed": np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        "outdated_software_count": np.random.randint(0, 5, n_samples),
        "has_default_credentials": np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        "breach_history_count": np.random.randint(0, 10, n_samples),
        "http_security_headers_score": np.random.randint(0, 6, n_samples),
        "exposure_type_score": np.random.randint(1, 6, n_samples),
    }

    df = pd.DataFrame(data)

    # Calculate risk score based on weighted features
    risk_scores = []
    for _, row in df.iterrows():
        score = 0

        score += row["open_ports_count"] * 3
        score += row["has_ssh_open"] * 15
        score += row["has_rdp_open"] * 25
        score += row["has_database_ports_open"] * 30

        # SSL days penalty
        if row["ssl_days_until_expiry"] < 0:
            score += 35  # Expired
        elif row["ssl_days_until_expiry"] < 30:
            score += 20  # Expiring soon

        score += row["ssl_cert_is_self_signed"] * 10
        score += row["outdated_software_count"] * 8
        score += row["has_default_credentials"] * 40
        score += row["breach_history_count"] * 5
        score += (5 - row["http_security_headers_score"]) * 4
        score += row["exposure_type_score"] * 5

        risk_scores.append(min(score, 100))

    df["risk_score"] = risk_scores

    # Convert to classification problem (4 classes)
    def score_to_class(score):
        if score >= 86:
            return 3  # critical
        elif score >= 61:
            return 2  # high
        elif score >= 31:
            return 1  # medium
        else:
            return 0  # low

    df["risk_class"] = df["risk_score"].apply(score_to_class)

    return df


def train_model(df):
    """
    Train logistic regression model for risk classification.

    Args:
        df: DataFrame with features and risk_class label

    Returns:
        Trained model and scaler
    """
    logger.info("Training model...")

    # Features and labels
    X = df.drop(["risk_score", "risk_class"], axis=1)
    y = df["risk_class"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train logistic regression
    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"Model accuracy: {accuracy:.4f}")
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred, target_names=["low", "medium", "high", "critical"]))

    return model, scaler


def save_model(model, scaler, models_dir="backend/app/ml/models"):
    """
    Save trained model and scaler to disk.

    Args:
        model: Trained model
        scaler: Fitted scaler
        models_dir: Directory to save models
    """
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "risk_model.joblib")
    scaler_path = os.path.join(models_dir, "scaler.joblib")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")


def main():
    """Main training pipeline."""
    logger.info("Starting ML model training...")

    # Generate synthetic data
    df = generate_synthetic_data(n_samples=10000)

    # Train model
    model, scaler = train_model(df)

    # Save model
    save_model(model, scaler)

    logger.info("Training complete!")


if __name__ == "__main__":
    main()
