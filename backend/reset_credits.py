import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.database import connect_to_mongodb, get_collection

async def reset_scan_credits():
    """Reset scan credits for all users"""
    try:
        # Connect to MongoDB
        await connect_to_mongodb()
        print("✅ Connected to MongoDB")
        
        # Get users collection
        users_collection = get_collection("users")
        
        # Reset credits for all users
        result = await users_collection.update_many(
            {}, 
            {
                "$set": {
                    "scan_credits_used": 0, 
                    "scan_credits_limit": 100
                }
            }
        )
        
        print(f"✅ Scan credits reset for {result.modified_count} users")
        print("🎉 100 scan credits available for each user")
        
    except Exception as e:
        print(f"❌ Error resetting scan credits: {e}")

if __name__ == "__main__":
    asyncio.run(reset_scan_credits())