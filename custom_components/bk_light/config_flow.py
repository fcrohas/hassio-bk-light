"""Config flow for BK Light ACT1026 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ADDRESS,
    CONF_BRIGHTNESS,
    CONF_ROTATION,
    DEFAULT_BRIGHTNESS,
    DEFAULT_NAME,
    DEFAULT_ROTATION,
    DOMAIN,
)
from .bk_light_device import BKLightDevice

_LOGGER = logging.getLogger(__name__)

# Bluetooth MAC address validation
def is_valid_mac_address(address: str) -> bool:
    """Validate MAC address format."""
    parts = address.split(":")
    if len(parts) != 6:
        return False
    try:
        for part in parts:
            if len(part) != 2:
                return False
            int(part, 16)
        return True
    except ValueError:
        return False


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ROTATION, default=DEFAULT_ROTATION): vol.In([0, 90, 180, 270]),
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=1.0)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    address = data[CONF_ADDRESS].upper()
    
    if not is_valid_mac_address(address):
        raise ValueError("Invalid Bluetooth MAC address format")
    
    rotation = data.get(CONF_ROTATION, DEFAULT_ROTATION)
    brightness = data.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS)

    device = BKLightDevice(address, rotation, brightness)

    # Test connection
    try:
        connected = await device.connect()
        if not connected:
            raise ConnectionError("Failed to connect to device")
        await device.disconnect()
    except Exception as err:
        _LOGGER.error("Failed to connect to BK Light at %s - %s", address, err)
        raise ConnectionError(f"Cannot connect to device: {err}") from err

    return {"title": data.get(CONF_NAME, DEFAULT_NAME)}


class BKLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BK Light ACT1026."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Normalize MAC address
            user_input[CONF_ADDRESS] = user_input[CONF_ADDRESS].upper()
            
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_address"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BKLightOptionsFlowHandler:
        """Get the options flow for this handler."""
        return BKLightOptionsFlowHandler(config_entry)


class BKLightOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for BK Light."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=self.config_entry.data.get(CONF_NAME, DEFAULT_NAME),
                    ): cv.string,
                    vol.Optional(
                        CONF_ROTATION,
                        default=self.config_entry.data.get(CONF_ROTATION, DEFAULT_ROTATION),
                    ): vol.In([0, 90, 180, 270]),
                    vol.Optional(
                        CONF_BRIGHTNESS,
                        default=self.config_entry.data.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
                }
            ),
        )
