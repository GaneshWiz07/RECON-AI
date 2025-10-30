"""
Firebase authentication middleware for FastAPI.

This middleware intercepts all requests and validates Firebase ID tokens,
except for public routes. It attaches user information to request.state.user
for use in route handlers.
"""

import logging
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.firebase import verify_firebase_token

logger = logging.getLogger(__name__)

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
]

# Route prefixes that don't require authentication
PUBLIC_PREFIXES = [
    "/api/webhooks",  # Stripe webhooks use signature verification
]


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify Firebase authentication tokens on all protected routes.

    Public routes and webhook endpoints are exempted from authentication.
    Protected routes must include a valid Firebase ID token in the
    Authorization header (format: Bearer <token>).

    On successful verification, user information is attached to request.state.user.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and verify Firebase token if required.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response from the route handler or error response
        """
        # Check if route is public
        if self._is_public_route(request.url.path):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"No Authorization header for protected route: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "No authentication token provided",
                }
            )

        # Verify Bearer token format
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Invalid Authorization header format: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Invalid authorization header format. Use: Bearer <token>",
                }
            )

        # Extract token
        token = auth_header.split("Bearer ", 1)[1].strip()

        if not token:
            logger.warning(f"Empty token in Authorization header: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Authentication token is empty",
                }
            )

        try:
            # Verify Firebase token
            user_info = await verify_firebase_token(token)

            # Attach user info to request state
            request.state.user = user_info

            logger.debug(
                f"Authenticated request for user {user_info['uid']} "
                f"to {request.url.path}"
            )

            # Continue to route handler
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Firebase token verification failed
            logger.warning(
                f"Token verification failed for {request.url.path}: {e.detail}"
            )
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "Unauthorized",
                    "detail": e.detail,
                }
            )

        except Exception as e:
            # Unexpected error
            logger.error(
                f"Unexpected error in auth middleware for {request.url.path}: {str(e)}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "detail": "Authentication verification failed",
                }
            )

    def _is_public_route(self, path: str) -> bool:
        """
        Check if a route is public (doesn't require authentication).

        Args:
            path: Request path

        Returns:
            True if route is public, False otherwise
        """
        # Exact match for public routes
        if path in PUBLIC_ROUTES:
            return True

        # Prefix match for public route groups
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False


def get_current_user(request: Request) -> dict:
    """
    Get the current authenticated user from request state.

    This function should be used in route handlers to access user information
    after the authentication middleware has verified the token.

    Args:
        request: FastAPI request object

    Returns:
        Dict with user information:
        {
            "uid": "firebase_uid",
            "email": "user@example.com",
            "email_verified": bool,
            "name": "User Name",
            "picture": "https://..."
        }

    Raises:
        HTTPException: 401 if user is not authenticated

    Usage in route handlers:
        @app.get("/api/protected-route")
        async def protected_route(request: Request):
            user = get_current_user(request)
            return {"user_id": user["uid"]}
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. This route requires authentication."
        )

    return request.state.user
