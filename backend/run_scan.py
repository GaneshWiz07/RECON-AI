import sys
import asyncio
from app.tasks.scan_worker import _execute_scan_async

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python run_scan.py <scan_id> <domain> <user_id>")
        sys.exit(1)
    
    scan_id = sys.argv[1]
    domain = sys.argv[2]
    user_id = sys.argv[3]
    
    print(f"Running scan {scan_id} for {domain}")
    asyncio.run(_execute_scan_async(scan_id, domain, user_id))
    print("Scan completed!")