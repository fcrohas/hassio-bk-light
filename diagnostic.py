#!/usr/bin/env python3
"""
BK Light ACT1026 Diagnostic Tool
Run this script to test BLE connectivity to your BK Light device.

Usage:
    python3 diagnostic.py
    python3 diagnostic.py CC:42:DE:9A:B7:3B
"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient

UUID_WRITE = "0000fa02-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000fa03-0000-1000-8000-00805f9b34fb"


async def scan_devices():
    """Scan for all BLE devices."""
    print("=" * 70)
    print("BK Light ACT1026 Diagnostic Tool")
    print("=" * 70)
    print("\nScanning for BLE devices (15 seconds)...\n")
    
    try:
        devices = await BleakScanner.discover(timeout=15.0)
        
        print(f"Found {len(devices)} BLE devices total\n")
        print("-" * 70)
        
        # Look for BK Light devices
        led_devices = [
            d for d in devices 
            if d.name and any(prefix in d.name for prefix in ["LED_BLE", "BK_LIGHT", "BJ_LED"])
        ]
        
        if led_devices:
            print(f"✓ Found {len(led_devices)} BK Light device(s):\n")
            for device in led_devices:
                rssi = getattr(device, 'rssi', None)
                signal = "Excellent" if rssi and rssi > -60 else \
                        "Good" if rssi and rssi > -75 else \
                        "Fair" if rssi and rssi > -85 else "Weak"
                
                print(f"  Device Name:    {device.name}")
                print(f"  MAC Address:    {device.address}")
                if rssi:
                    print(f"  Signal (RSSI):  {rssi} dBm ({signal})")
                print(f"  {'-' * 66}")
        else:
            print("✗ No BK Light devices found!\n")
            print("Troubleshooting:")
            print("  • Make sure the display is powered on")
            print("  • Device should be within 10 meters")
            print("  • Disconnect from mobile app if connected")
            print("  • Try power cycling the display\n")
        
        # Show all devices
        print("\nAll BLE devices discovered:")
        print("-" * 70)
        for device in sorted(devices, key=lambda d: getattr(d, 'rssi', -100), reverse=True):
            name = device.name or "<Unnamed>"
            rssi = getattr(device, 'rssi', None)
            rssi_str = f"{rssi:4d} dBm" if rssi else "  N/A"
            print(f"  {name[:40]:<40} {device.address}  {rssi_str}")
        
        return led_devices
        
    except Exception as err:
        print(f"\n✗ Error during scan: {err}")
        print("\nThis may indicate:")
        print("  • Bluetooth adapter is not available")
        print("  • Insufficient permissions (try with sudo)")
        print("  • Bluetooth service is not running")
        print("\nTry:")
        print("  sudo hciconfig hci0 up")
        print("  sudo systemctl start bluetooth")
        return []


async def test_connection(address: str):
    """Test connection to a specific device."""
    print("\n" + "=" * 70)
    print(f"Testing connection to {address}...")
    print("=" * 70 + "\n")
    
    try:
        print("Step 1: Scanning for device...")
        device = await BleakScanner.find_device_by_address(address, timeout=15.0)
        
        if device is None:
            print(f"✗ Device {address} not found!")
            print("\nPossible issues:")
            print("  • Wrong MAC address")
            print("  • Device is off or out of range")
            print("  • Device is connected to another device")
            return False
        
        print(f"✓ Device found: {getattr(device, 'name', 'Unknown')}")
        
        print("\nStep 2: Connecting...")
        async with BleakClient(device, timeout=20.0) as client:
            print(f"✓ Connected successfully!")
            
            print("\nStep 3: Checking services...")
            services = await client.get_services()
            
            has_write = any(UUID_WRITE in str(s.uuid) for s in services.characteristics)
            has_notify = any(UUID_NOTIFY in str(s.uuid) for s in services.characteristics)
            
            if has_write:
                print(f"✓ Write characteristic found: {UUID_WRITE}")
            else:
                print(f"✗ Write characteristic NOT found!")
            
            if has_notify:
                print(f"✓ Notify characteristic found: {UUID_NOTIFY}")
            else:
                print(f"✗ Notify characteristic NOT found!")
            
            if has_write and has_notify:
                print("\n✓ Device appears to be a valid BK Light ACT1026!")
                print("  You can use this MAC address in Home Assistant")
                return True
            else:
                print("\n✗ Device does not have expected characteristics")
                print("  This may not be a BK Light ACT1026")
                return False
                
    except Exception as err:
        print(f"\n✗ Connection failed: {err}")
        print("\nPossible issues:")
        print("  • Device is already connected elsewhere")
        print("  • Bluetooth permissions issue")
        print("  • Device firmware issue")
        return False


async def main():
    """Main function."""
    # Check if MAC address provided
    if len(sys.argv) > 1:
        address = sys.argv[1].upper()
        await test_connection(address)
    else:
        # Just scan
        led_devices = await scan_devices()
        
        if led_devices:
            print("\n" + "=" * 70)
            print("Next steps:")
            print("=" * 70)
            print("\nTo test connection to a specific device, run:")
            for device in led_devices:
                print(f"  python3 diagnostic.py {device.address}")
        
    print("\n" + "=" * 70)
    print("Diagnostic complete")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
