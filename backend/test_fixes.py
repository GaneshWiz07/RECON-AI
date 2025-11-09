"""
Test script to verify the fixes for breach detection and port scanning.

Run this script to test:
1. BreachDirectory API integration
2. Port scanning with nmap/masscan/Python fallback
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.enrichers import check_breach_history, scan_ports
from app.collectors.port_scanner import PortScanner


async def test_breach_detection():
    """Test breach detection with HaveIBeenPwned API + fallback"""
    print("\n" + "="*60)
    print("🔍 Testing Breach Detection (HaveIBeenPwned API + Fallback)")
    print("="*60)
    
    test_domains = [
        ("adobe.com", "Known breached domain (should show breaches)"),
        ("linkedin.com", "Known breached domain (should show breaches)"),
        ("example.com", "Clean domain (should show 0)"),
    ]
    
    for domain, description in test_domains:
        print(f"\n📧 Testing: {domain} ({description})")
        try:
            breach_count = await check_breach_history(domain)
            if breach_count > 0:
                print(f"   ✅ Found {breach_count} breaches")
            else:
                print(f"   ℹ️  No breaches found")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


async def test_port_scanning():
    """Test port scanning with different methods"""
    print("\n" + "="*60)
    print("🔌 Testing Port Scanning")
    print("="*60)
    
    # Check available tools
    tools = PortScanner.check_tool_availability()
    print(f"\n📦 Available Tools:")
    print(f"   - Nmap: {'✅ Installed' if tools['nmap'] else '❌ Not installed'}")
    print(f"   - Masscan: {'✅ Installed' if tools['masscan'] else '❌ Not installed'}")
    print(f"   - Python Socket: ✅ Always available (fallback)")
    
    # Test targets
    test_targets = [
        ("scanme.nmap.org", "common", "Nmap's official test server"),
        ("google.com", "common", "Google (should have 80, 443)"),
    ]
    
    for target, scan_type, description in test_targets:
        print(f"\n🎯 Scanning: {target} ({description})")
        print(f"   Scan type: {scan_type}")
        
        try:
            result = await scan_ports(target, scan_type=scan_type)
            
            print(f"   Method used: {result['scan_method']}")
            print(f"   Duration: {result['scan_duration']:.2f} seconds")
            
            if result.get('error'):
                print(f"   ⚠️  Warning: {result['error']}")
            
            if result['open_ports']:
                print(f"   ✅ Open ports ({len(result['open_ports'])}): {result['open_ports']}")
                
                # Show services if available
                if result.get('services'):
                    print(f"   📋 Services detected:")
                    for port, service in result['services'].items():
                        print(f"      - Port {port}: {service.get('name', 'unknown')} "
                              f"{service.get('product', '')} {service.get('version', '')}")
            else:
                print(f"   ℹ️  No open ports detected")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


async def test_integration():
    """Test both fixes together (simulating real scan)"""
    print("\n" + "="*60)
    print("🔄 Integration Test (Simulating Real Scan)")
    print("="*60)
    
    test_domain = "example.com"
    print(f"\n🌐 Scanning: {test_domain}")
    
    # Simulate the scan workflow
    print("\n1️⃣ Checking breach history...")
    breach_count = await check_breach_history(test_domain)
    print(f"   Breaches found: {breach_count}")
    
    print("\n2️⃣ Scanning ports...")
    port_result = await scan_ports(test_domain, scan_type="common")
    print(f"   Method: {port_result['scan_method']}")
    print(f"   Open ports: {port_result['open_ports']}")
    
    print("\n✅ Integration test complete!")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 RECON-AI Fixes Verification Test Suite")
    print("="*60)
    print("\nThis script tests:")
    print("  1. BreachDirectory API integration (Fix #1)")
    print("  2. Port scanning with nmap/masscan (Fix #2)")
    print("  3. Integration of both fixes")
    
    try:
        # Test breach detection
        await test_breach_detection()
        
        # Test port scanning
        await test_port_scanning()
        
        # Test integration
        await test_integration()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        print("\n📝 Notes:")
        print("  - If breach counts are 0, the API might be rate limiting")
        print("  - If no ports found, check firewall/network settings")
        print("  - Python fallback is slower but always works")
        print("  - Install nmap/masscan for best performance")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
