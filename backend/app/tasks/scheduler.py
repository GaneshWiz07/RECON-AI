"""
Automated Rescan Scheduler

Runs periodically to trigger rescans for assets with rescan_enabled=True
"""

import asyncio
import logging
from datetime import datetime
from app.core.database import get_collection, connect_to_mongodb
from app.core.redis_client import connect_to_redis, get_redis_queue
from app.tasks.scan_worker import execute_scan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def rescan_scheduler():
    """
    Find assets that need rescanning and queue scan jobs.

    Runs every hour to check for assets where:
    - rescan_enabled = True
    - next_scan_at <= now
    """
    logger.info("Starting rescan scheduler...")

    try:
        # Connect to database
        await connect_to_mongodb()
        connect_to_redis()

        assets_collection = get_collection("assets")
        scans_collection = get_collection("scans")
        queue = get_redis_queue()

        # Find assets that need rescanning
        now = datetime.utcnow()
        assets_to_rescan = await assets_collection.find({
            "rescan_enabled": True,
            "next_scan_at": {"$lte": now}
        }).to_list(length=1000)

        logger.info(f"Found {len(assets_to_rescan)} assets to rescan")

        for asset in assets_to_rescan:
            try:
                # Create scan record
                scan_id = f"scn_{datetime.utcnow().timestamp()}_rescan"
                scan_doc = {
                    "scan_id": scan_id,
                    "user_id": asset["user_id"],
                    "workspace_id": asset["workspace_id"],
                    "asset_id": asset["asset_id"],
                    "domain": asset["asset_value"],
                    "scan_type": "rescan",
                    "scan_status": "pending",
                    "created_at": datetime.utcnow(),
                }

                await scans_collection.insert_one(scan_doc)

                # Queue scan job
                queue.enqueue(execute_scan, scan_id, asset["asset_value"], asset["user_id"])

                # Update next_scan_at based on frequency
                from datetime import timedelta
                if asset["rescan_frequency"] == "daily":
                    next_scan = now + timedelta(days=1)
                elif asset["rescan_frequency"] == "weekly":
                    next_scan = now + timedelta(weeks=1)
                else:
                    next_scan = None

                if next_scan:
                    await assets_collection.update_one(
                        {"asset_id": asset["asset_id"]},
                        {"$set": {"next_scan_at": next_scan}}
                    )

                logger.info(f"Queued rescan for asset {asset['asset_id']}")

            except Exception as e:
                logger.error(f"Failed to queue rescan for asset {asset.get('asset_id')}: {str(e)}")
                continue

        logger.info("Rescan scheduler completed")

    except Exception as e:
        logger.error(f"Rescan scheduler failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(rescan_scheduler())
