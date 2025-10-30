"""
Firebase Admin SDK initialization and token verification.

This module initializes the Firebase Admin SDK with service account credentials
from environment variables and provides token verification functionality.
"""

import os
import logging
from typing import Dict, Optional
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK with service account credentials.

    Credentials are loaded from environment variables:
    - FIREBASE_PROJECT_ID
    - FIREBASE_PRIVATE_KEY
    - FIREBASE_CLIENT_EMAIL

    Raises:
        ValueError: If required environment variables are missing.
    """
    global _firebase_app

    if _firebase_app is not None:
        logger.info("Firebase already initialized")
        return

    try:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

        if not all([project_id, private_key, client_email]):
            raise ValueError(
                "Missing required Firebase credentials. "
                "Please set FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, and FIREBASE_CLIENT_EMAIL"
            )

        # Handle escaped newlines in private key
        if private_key:
            private_key = private_key.replace('\\n', '\n')

        cred_dict = {
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
        }

        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)

        logger.info(f"Firebase Admin SDK initialized successfully for project: {project_id}")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        raise


async def verify_firebase_token(token: str) -> Dict:
    """
    Verify Firebase ID token and return decoded user information.

    Args:
        token: Firebase ID token string

    Returns:
        Dict containing user information:
        {
            "uid": "firebase_uid",
            "email": "user@example.com",
            "email_verified": bool,
            "name": "User Name",
            "picture": "https://..."
        }

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    if not token:
        raise HTTPException(
            status_code=401,
            detail="No authentication token provided"
        )

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)

        # Extract user information
        user_info = {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }

        logger.debug(f"Token verified successfully for user: {user_info['uid']}")
        return user_info

    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token")
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except auth.RevokedIdTokenError:
        logger.warning("Revoked Firebase ID token")
        raise HTTPException(
            status_code=401,
            detail="Authentication token has been revoked"
        )
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Failed to verify authentication token"
        )


def get_firebase_app() -> firebase_admin.App:
    """
    Get the initialized Firebase app instance.

    Returns:
        Firebase app instance

    Raises:
        RuntimeError: If Firebase has not been initialized
    """
    if _firebase_app is None:
        raise RuntimeError(
            "Firebase has not been initialized. "
            "Call initialize_firebase() first."
        )
    return _firebase_app
