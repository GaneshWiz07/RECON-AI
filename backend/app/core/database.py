"""
MongoDB database connection and initialization.

This module handles async MongoDB connections using Motor driver
and provides access to collections with proper indexing.
"""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Global database connection
_mongo_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """
    Initialize MongoDB connection using Motor (async driver).

    Connects to MongoDB Atlas using MONGO_URI environment variable.

    Raises:
        ValueError: If MONGO_URI is not set
        Exception: If connection fails
    """
    global _mongo_client, _database

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set")

    try:
        _mongo_client = AsyncIOMotorClient(
            mongo_uri,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,
        )

        # Get database name from URI or use default
        _database = _mongo_client.get_default_database()
        if _database is None:
            _database = _mongo_client["reconai"]

        # Test connection
        await _mongo_client.admin.command("ping")

        logger.info(f"Successfully connected to MongoDB: {_database.name}")

        # Create indexes
        await create_indexes()

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")


async def create_indexes() -> None:
    """
    Create database indexes for optimal query performance.

    Creates indexes on:
    - users: uid (unique), email (unique), stripe_customer_id
    - assets: user_id + asset_value (compound unique), next_scan_at, risk_score
    - scans: asset_id + created_at (compound), user_id, scan_status
    - billing_events: user_id + created_at, stripe_event_id (unique)
    - api_usage_logs: user_id + timestamp, timestamp (TTL 90 days)
    """
    db = get_database()

    try:
        # Users collection indexes
        await db.users.create_index("uid", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("stripe_customer_id")

        # Assets collection indexes
        await db.assets.create_index([("user_id", 1), ("asset_value", 1)], unique=True)
        await db.assets.create_index("workspace_id")
        await db.assets.create_index([("risk_score", -1)])  # Descending for top risky assets
        await db.assets.create_index("next_scan_at")  # For scheduler queries
        await db.assets.create_index("asset_type")

        # Scans collection indexes
        await db.scans.create_index([("asset_id", 1), ("created_at", -1)])
        await db.scans.create_index("user_id")
        await db.scans.create_index("scan_status")
        await db.scans.create_index([("created_at", -1)])

        # Billing events collection indexes
        await db.billing_events.create_index([("user_id", 1), ("created_at", -1)])
        await db.billing_events.create_index("stripe_event_id", unique=True)

        # API usage logs collection indexes with TTL (90 days)
        await db.api_usage_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await db.api_usage_logs.create_index(
            "timestamp",
            expireAfterSeconds=7776000  # 90 days in seconds
        )

        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        # Don't raise - indexes might already exist


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.

    Returns:
        AsyncIOMotorDatabase instance

    Raises:
        RuntimeError: If database connection is not initialized
    """
    if _database is None:
        raise RuntimeError(
            "Database connection not initialized. "
            "Call connect_to_mongodb() first."
        )
    return _database


def get_collection(collection_name: str):
    """
    Get a MongoDB collection by name.

    Args:
        collection_name: Name of the collection

    Returns:
        AsyncIOMotorCollection instance

    Available collections:
    - users
    - assets
    - scans
    - billing_events
    - api_usage_logs
    """
    db = get_database()
    return db[collection_name]


async def check_database_health() -> dict:
    """
    Check database connection health.

    Returns:
        Dict with connection status and stats
    """
    try:
        if _mongo_client is None:
            return {"status": "disconnected", "error": "No client initialized"}

        # Ping database
        await _mongo_client.admin.command("ping")

        # Get database stats
        db = get_database()
        stats = await db.command("dbStats")

        return {
            "status": "connected",
            "database": db.name,
            "collections": stats.get("collections", 0),
            "dataSize": stats.get("dataSize", 0),
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
