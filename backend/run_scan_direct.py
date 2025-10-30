import sys
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database and other components
from app.core.database import connect_to_mongodb
from app.core.firebase import initialize_firebase
from app.tasks.scan_worker import _execute_scan_async

async def main():
    if len(sys.argv) != 4:
        print("Usage: python run_scan_direct.py <scan_id> <domain> <user_id>")
        return
    
    scan_id = sys.argv[1]
    domain = sys.argv[2]
    user_id = sys.argv[3]
    
    print(f"Initializing components...")
    
    # Initialize Firebase
    try:
        initialize_firebase()
        print("✓ Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase initialization warning: {e}")
    
    # Initialize MongoDB
    try:
        await connect_to_mongodb()
        print("✓ MongoDB connected")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    print(f"Running scan {scan_id} for {domain}")
    await _execute_scan_async(scan_id, domain, user_id)
    print("Scan completed!")

if __name__ == "__main__":
    asyncio.run(main())