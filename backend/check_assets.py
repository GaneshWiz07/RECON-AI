"""
Check assets in database
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.core.database import connect_to_mongodb, get_collection

async def check_assets():
    await connect_to_mongodb()
    
    assets = get_collection("assets")
    scans = get_collection("scans")
    
    asset_count = await assets.count_documents({})
    scan_count = await scans.count_documents({})
    
    print(f"\n=== Database Status ===")
    print(f"Total Assets: {asset_count}")
    print(f"Total Scans: {scan_count}")
    
    if scan_count > 0:
        print(f"\n=== Recent Scans ===")
        recent_scans = await scans.find().sort("created_at", -1).limit(5).to_list(length=5)
        for scan in recent_scans:
            print(f"\nScan ID: {scan.get('scan_id')}")
            print(f"  Domain: {scan.get('domain')}")
            print(f"  Status: {scan.get('scan_status')}")
            print(f"  User ID: {scan.get('user_id')}")
            print(f"  Assets Found: {scan.get('assets_found', 'N/A')}")
            if scan.get('error_message'):
                print(f"  Error: {scan.get('error_message')}")
    
    if asset_count > 0:
        print(f"\n=== Recent Assets ===")
        recent_assets = await assets.find().sort("discovered_at", -1).limit(5).to_list(length=5)
        for asset in recent_assets:
            print(f"\nAsset: {asset.get('asset_value')}")
            print(f"  Type: {asset.get('asset_type')}")
            print(f"  Risk Score: {asset.get('risk_score')}")
            print(f"  User ID: {asset.get('user_id')}")
            print(f"  Discovered At: {asset.get('discovered_at')}")
            print(f"  Last Scanned At: {asset.get('last_scanned_at')}")
            print(f"  Created At: {asset.get('created_at')}")
            print(f"  Updated At: {asset.get('updated_at')}")
            print(f"  Status fields: {[k for k in asset.keys() if 'status' in k.lower()]}")

if __name__ == "__main__":
    asyncio.run(check_assets())

