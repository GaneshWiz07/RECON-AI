"""
Authentication API routes.

Handles user registration, login, and profile retrieval.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.core.database import get_collection
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Response models
class UserResponse(BaseModel):
    """User profile response model."""
    uid: str
    email: str
    display_name: str | None = None
    photo_url: str | None = None
    plan: str
    api_calls_used: int
    api_calls_limit: int
    scan_credits_used: int
    scan_credits_limit: int
    usage_reset_at: datetime
    created_at: datetime


class RegisterResponse(BaseModel):
    """Registration response model."""
    data: Dict
    message: str


class LoginResponse(BaseModel):
    """Login response model."""
    data: Dict
    message: str


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register_user(request: Request):
    """
    Create new user account after Firebase signup.

    User info is extracted from the verified Firebase token (set by middleware).
    Creates user document in MongoDB with default free plan values.

    Returns:
        201: User registered successfully
        409: User already exists
        500: Database error
    """
    # Get user info from Firebase token (verified by middleware)
    user_info = get_current_user(request)
    uid = user_info["uid"]
    email = user_info["email"]

    try:
        users_collection = get_collection("users")

        # Check if user already exists
        existing_user = await users_collection.find_one({"uid": uid})
        if existing_user:
            logger.warning(f"Attempted to register existing user: {uid}")
            raise HTTPException(
                status_code=409,
                detail="User already exists"
            )

        # Create new user document
        now = datetime.utcnow()
        usage_reset_at = now + timedelta(days=30)

        user_doc = {
            "uid": uid,
            "email": email,
            "display_name": user_info.get("name"),
            "photo_url": user_info.get("picture"),
            "email_verified": user_info.get("email_verified", False),
            # Workspace (merged with user since 1:1 relationship)
            "workspace_id": uid,  # Same as uid
            # Subscription & Billing
            "plan": "free",
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "subscription_status": "active",
            # Usage Tracking
            "api_calls_used": 0,
            "api_calls_limit": 100,  # Free tier
            "scan_credits_used": 0,
            "scan_credits_limit": 10,  # Free tier
            "usage_reset_at": usage_reset_at,
            # Timestamps
            "created_at": now,
            "last_login_at": now,
            "updated_at": now,
        }

        result = await users_collection.insert_one(user_doc)

        logger.info(f"New user registered: {uid} ({email})")

        # Remove MongoDB _id from response
        user_doc.pop("_id", None)

        return {
            "data": {
                "user": {
                    "uid": user_doc["uid"],
                    "email": user_doc["email"],
                    "display_name": user_doc["display_name"],
                    "photo_url": user_doc["photo_url"],
                    "plan": user_doc["plan"],
                    "api_calls_used": user_doc["api_calls_used"],
                    "api_calls_limit": user_doc["api_calls_limit"],
                    "scan_credits_used": user_doc["scan_credits_used"],
                    "scan_credits_limit": user_doc["scan_credits_limit"],
                    "created_at": user_doc["created_at"].isoformat(),
                }
            },
            "message": "User registered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register user {uid}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(request: Request):
    """
    Sync user data on login (creates user if first OAuth login).

    If user doesn't exist (e.g., first Google OAuth login), creates new user.
    If user exists, updates last_login_at timestamp.

    Returns:
        200: Login successful
        401: Invalid token (handled by middleware)
        500: Database error
    """
    # Get user info from Firebase token (verified by middleware)
    user_info = get_current_user(request)
    uid = user_info["uid"]
    email = user_info["email"]

    try:
        users_collection = get_collection("users")

        # Check if user exists
        existing_user = await users_collection.find_one({"uid": uid})

        if existing_user:
            # User exists - update last login
            await users_collection.update_one(
                {"uid": uid},
                {
                    "$set": {
                        "last_login_at": datetime.utcnow(),
                        "display_name": user_info.get("name") or existing_user.get("display_name"),
                        "photo_url": user_info.get("picture") or existing_user.get("photo_url"),
                    }
                }
            )

            # Fetch updated user
            user = await users_collection.find_one({"uid": uid})
            logger.info(f"User logged in: {uid} ({email})")

        else:
            # First time OAuth login - create user
            now = datetime.utcnow()
            usage_reset_at = now + timedelta(days=30)

            user_doc = {
                "uid": uid,
                "email": email,
                "display_name": user_info.get("name"),
                "photo_url": user_info.get("picture"),
                "email_verified": user_info.get("email_verified", False),
                "workspace_id": uid,
                "plan": "free",
                "stripe_customer_id": None,
                "stripe_subscription_id": None,
                "subscription_status": "active",
                "api_calls_used": 0,
                "api_calls_limit": 100,
                "scan_credits_used": 0,
                "scan_credits_limit": 10,
                "usage_reset_at": usage_reset_at,
                "created_at": now,
                "last_login_at": now,
                "updated_at": now,
            }

            await users_collection.insert_one(user_doc)
            user = user_doc

            logger.info(f"New user created via OAuth: {uid} ({email})")

        # Remove MongoDB _id from response
        user.pop("_id", None)

        return {
            "data": {
                "user": {
                    "uid": user["uid"],
                    "email": user["email"],
                    "display_name": user.get("display_name"),
                    "photo_url": user.get("photo_url"),
                    "plan": user["plan"],
                    "subscription_status": user.get("subscription_status"),
                    "api_calls_used": user["api_calls_used"],
                    "api_calls_limit": user["api_calls_limit"],
                    "scan_credits_used": user["scan_credits_used"],
                    "scan_credits_limit": user["scan_credits_limit"],
                },
                "workspace_id": user["workspace_id"]
            },
            "message": "Login successful"
        }

    except Exception as e:
        logger.error(f"Login failed for user {uid}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process login"
        )


@router.get("/me")
async def get_current_user_profile(request: Request):
    """
    Get current user profile.

    Returns user information including subscription and usage details.

    Returns:
        200: User profile
        401: Not authenticated
        404: User not found
    """
    # Get user info from Firebase token (verified by middleware)
    user_info = get_current_user(request)
    uid = user_info["uid"]

    try:
        users_collection = get_collection("users")

        # Fetch user from database
        user = await users_collection.find_one({"uid": uid})

        if not user:
            logger.error(f"User not found in database: {uid}")
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Remove MongoDB _id from response
        user.pop("_id", None)

        return {
            "data": {
                "user": {
                    "uid": user["uid"],
                    "email": user["email"],
                    "display_name": user.get("display_name"),
                    "photo_url": user.get("photo_url"),
                    "plan": user["plan"],
                    "subscription_status": user.get("subscription_status"),
                    "api_calls_used": user["api_calls_used"],
                    "api_calls_limit": user["api_calls_limit"],
                    "scan_credits_used": user["scan_credits_used"],
                    "scan_credits_limit": user["scan_credits_limit"],
                    "usage_reset_at": user["usage_reset_at"].isoformat() if user.get("usage_reset_at") else None,
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user profile {uid}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch user profile"
        )
