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
        _LOGGER.info("Scanning for BLE devices with LED_BLE prefix...")
        
        try:
            devices = await BleakScanner.discover(timeout=10.0)
            
            led_devices = [
                d for d in devices 
                if d.name and (
                    d.name.startswith("LED_BLE_") or 
                    d.name.startswith("BK_LIGHT") or 
                    d.name.startswith("BJ_LED")
                )
            ]
            
            if led_devices:
                _LOGGER.info("Found %d BK Light devices:", len(led_devices))
                for device in led_devices:
                    _LOGGER.info(
                        "  - %s at %s (RSSI: %s dBm)",
                        device.name,
                        device.address,
                        device.rssi if hasattr(device, 'rssi') else 'N/A'
                    )
            else:
                _LOGGER.warning(
                    "No BK Light devices found. Make sure the display is powered on "
                    "and in Bluetooth range."
                )
                
            # Also log all BLE devices for debugging
            _LOGGER.debug("All BLE devices found:")
            for device in devices:
                _LOGGER.debug(
                    "  - %s at %s",
                    device.name or "Unknown",
                    device.address
                )
                
        except Exception as err:
            _LOGGER.error("Error scanning for devices: %s", err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_DEVICES,
        handle_scan_devices,
        schema=SERVICE_SCAN_DEVICES_SCHEMA,
    )
