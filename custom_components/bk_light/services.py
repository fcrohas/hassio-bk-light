"""Services for BK Light ACT1026 integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Final

from bleak import BleakScanner
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SCAN_DEVICES: Final = "scan_devices"

SERVICE_SCAN_DEVICES_SCHEMA = vol.Schema({})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for BK Light integration."""

    async def handle_scan_devices(call: ServiceCall) -> None:
        """Handle the scan_devices service call."""
        _LOGGER.info("=" * 60)
        _LOGGER.info("BK Light Device Scanner")
        _LOGGER.info("=" * 60)
        _LOGGER.info("Scanning for BLE devices (15 seconds)...")
        
        try:
            devices = await BleakScanner.discover(timeout=15.0)
            
            _LOGGER.info("Scan complete. Found %d BLE devices total.", len(devices))
            _LOGGER.info("-" * 60)
            
            # Filter for BK Light devices
            led_devices = [
                d for d in devices 
                if d.name and (
                    d.name.startswith("LED_BLE_") or 
                    d.name.startswith("BK_LIGHT") or 
                    d.name.startswith("BJ_LED")
                )
            ]
            
            if led_devices:
                _LOGGER.info("✓ Found %d BK Light device(s):", len(led_devices))
                _LOGGER.info("-" * 60)
                for device in led_devices:
                    rssi = getattr(device, 'rssi', None)
                    signal_strength = "Excellent" if rssi and rssi > -60 else \
                                    "Good" if rssi and rssi > -75 else \
                                    "Fair" if rssi and rssi > -85 else "Weak"
                    
                    _LOGGER.info("  Device Name:    %s", device.name)
                    _LOGGER.info("  MAC Address:    %s", device.address)
                    if rssi:
                        _LOGGER.info("  Signal (RSSI):  %d dBm (%s)", rssi, signal_strength)
                    _LOGGER.info("  " + "-" * 56)
            else:
                _LOGGER.warning("✗ No BK Light devices found!")
                _LOGGER.warning("Expected device names: LED_BLE_*, BK_LIGHT*, BJ_LED*")
                _LOGGER.warning("")
                _LOGGER.warning("Troubleshooting steps:")
                _LOGGER.warning("  1. Make sure the display is powered on")
                _LOGGER.warning("  2. Check the device is within 10 meters")
                _LOGGER.warning("  3. Disconnect from mobile app if connected")
                _LOGGER.warning("  4. Try power cycling the display")
                
            # Show all devices for debugging
            _LOGGER.info("")
            _LOGGER.info("All BLE devices found:")
            _LOGGER.info("-" * 60)
            for device in sorted(devices, key=lambda d: getattr(d, 'rssi', -100), reverse=True):
                name = device.name or "<Unnamed>"
                rssi = getattr(device, 'rssi', None)
                rssi_str = f"{rssi} dBm" if rssi else "N/A"
                _LOGGER.info("  %-30s %s  (RSSI: %s)", name[:30], device.address, rssi_str)
            
            _LOGGER.info("=" * 60)
            _LOGGER.info("Scan complete. Check the information above.")
            _LOGGER.info("=" * 60)
                
        except Exception as err:
            _LOGGER.error("=" * 60)
            _LOGGER.error("Error scanning for devices: %s", err)
            _LOGGER.error("This may indicate a Bluetooth adapter issue.")
            _LOGGER.error("Try: sudo hciconfig hci0 up")
            _LOGGER.error("=" * 60)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_DEVICES,
        handle_scan_devices,
        schema=SERVICE_SCAN_DEVICES_SCHEMA,
    )
