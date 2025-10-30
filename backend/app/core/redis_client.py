"""
Redis connection and queue management.

This module handles Redis connections for:
- Task queue (RQ - Redis Queue)
- Rate limiting
- Caching
"""

import os
import logging
from typing import Optional
import redis
from redis import Redis
from rq import Queue

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_client: Optional[Redis] = None
_redis_queue: Optional[Queue] = None


def connect_to_redis() -> None:
    """
    Initialize Redis connection.

    Connects using REDIS_URL environment variable.

    Raises:
        ValueError: If REDIS_URL is not set
        Exception: If connection fails
    """
    global _redis_client, _redis_queue

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is not set")

    try:
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        _redis_client.ping()

        # Initialize RQ queue for background tasks
        _redis_queue = Queue("scan_queue", connection=_redis_client)

        logger.info("Successfully connected to Redis")

    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise


def close_redis_connection() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        _redis_client.close()
        logger.info("Redis connection closed")


def get_redis_client() -> Redis:
    """
    Get the Redis client instance.

    Returns:
        Redis client instance

    Raises:
        RuntimeError: If Redis is not initialized
    """
    if _redis_client is None:
        raise RuntimeError(
            "Redis connection not initialized. "
            "Call connect_to_redis() first."
        )
    return _redis_client


def get_redis_queue() -> Queue:
    """
    Get the Redis Queue instance for background tasks.

    Returns:
        RQ Queue instance

    Raises:
        RuntimeError: If Redis queue is not initialized
    """
    if _redis_queue is None:
        raise RuntimeError(
            "Redis queue not initialized. "
            "Call connect_to_redis() first."
        )
    return _redis_queue


async def check_redis_health() -> dict:
    """
    Check Redis connection health.

    Returns:
        Dict with connection status and stats
    """
    try:
        if _redis_client is None:
            return {"status": "disconnected", "error": "No client initialized"}

        # Ping Redis
        _redis_client.ping()

        # Get info
        info = _redis_client.info()

        return {
            "status": "connected",
            "version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        }

    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# Rate limiting utilities

def check_rate_limit(key: str, limit: int, window_seconds: int = 3600) -> bool:
    """
    Check if a rate limit has been exceeded using sliding window.

    Args:
        key: Redis key for this rate limit (e.g., "rate_limit:user:uid:api_calls")
        limit: Maximum number of requests allowed
        window_seconds: Time window in seconds (default: 1 hour)

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    redis_client = get_redis_client()

    try:
        current = redis_client.get(key)

        if current is None:
            # First request - set counter to 1 with expiry
            redis_client.setex(key, window_seconds, 1)
            return True

        current_count = int(current)

        if current_count >= limit:
            return False  # Rate limit exceeded

        # Increment counter
        redis_client.incr(key)
        return True

    except Exception as e:
        logger.error(f"Rate limit check failed for key {key}: {str(e)}")
        # Fail open - allow request if rate limiting fails
        return True


def increment_rate_limit(key: str, window_seconds: int = 3600) -> int:
    """
    Increment a rate limit counter.

    Args:
        key: Redis key for this rate limit
        window_seconds: Time window in seconds

    Returns:
        Current count after increment
    """
    redis_client = get_redis_client()

    try:
        current = redis_client.get(key)

        if current is None:
            redis_client.setex(key, window_seconds, 1)
            return 1

        new_count = redis_client.incr(key)
        return new_count

    except Exception as e:
        logger.error(f"Failed to increment rate limit for key {key}: {str(e)}")
        return 0


def get_rate_limit_remaining(key: str, limit: int) -> dict:
    """
    Get remaining requests for a rate limit.

    Args:
        key: Redis key for this rate limit
        limit: Maximum number of requests allowed

    Returns:
        Dict with used, limit, remaining, and reset time
    """
    redis_client = get_redis_client()

    try:
        current = redis_client.get(key)
        used = int(current) if current else 0
        remaining = max(0, limit - used)

        # Get TTL for reset time
        ttl = redis_client.ttl(key)
        reset_in_seconds = ttl if ttl > 0 else 0

        return {
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "reset_in_seconds": reset_in_seconds,
        }

    except Exception as e:
        logger.error(f"Failed to get rate limit info for key {key}: {str(e)}")
        return {
            "used": 0,
            "limit": limit,
            "remaining": limit,
            "reset_in_seconds": 0,
        }


# Caching utilities

def cache_set(key: str, value: str, expiry_seconds: int = 3600) -> bool:
    """
    Set a cache value with expiry.

    Args:
        key: Cache key
        value: Value to cache
        expiry_seconds: Expiry time in seconds

    Returns:
        True if successful
    """
    redis_client = get_redis_client()

    try:
        redis_client.setex(key, expiry_seconds, value)
        return True
    except Exception as e:
        logger.error(f"Failed to set cache for key {key}: {str(e)}")
        return False


def cache_get(key: str) -> Optional[str]:
    """
    Get a cached value.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    redis_client = get_redis_client()

    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Failed to get cache for key {key}: {str(e)}")
        return None
