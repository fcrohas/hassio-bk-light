"""The BK Light ACT1026 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_ADDRESS, CONF_BRIGHTNESS, CONF_ROTATION, DEFAULT_BRIGHTNESS, DEFAULT_ROTATION, DOMAIN
from .bk_light_device import BKLightDevice
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.IMAGE]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the BK Light component."""
    await async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BK Light from a config entry."""
    address = entry.data[CONF_ADDRESS]
    rotation = entry.data.get(CONF_ROTATION, DEFAULT_ROTATION)
    brightness = entry.data.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS)

    device = BKLightDevice(address, rotation, brightness)
    
    try:
        if not await device.connect():
            raise ConfigEntryNotReady(f"Cannot connect to device at {address}")
    except Exception as err:
        _LOGGER.error("Failed to connect to BK Light at %s: %s", address, err)
        raise ConfigEntryNotReady(f"Cannot connect to device at {address}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        device = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
