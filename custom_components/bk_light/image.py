"""Platform for BK Light ACT1026 image display integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    MODEL_DESCRIPTION,
)
from .bk_light_device import BKLightDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BK Light from a config entry."""
    device: BKLightDevice = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([BKLightImageEntity(device, config_entry)], True)


class BKLightImageEntity(ImageEntity):
    """Representation of a BK Light ACT1026 display."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: BKLightDevice, config_entry: ConfigEntry) -> None:
        """Initialize the display."""
        super().__init__()
        self._device = device
        self._attr_unique_id = f"{config_entry.entry_id}_display"
        self._attr_image_url = None
        self._current_image: Image.Image | None = None
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            model_id=MODEL_DESCRIPTION,
        )

    async def async_image(self) -> bytes | None:
        """Return current image as bytes."""
        if self._current_image:
            buffer = BytesIO()
            self._current_image.save(buffer, format="PNG")
            return buffer.getvalue()
        
        # Return a default clock display
        return await self._generate_clock_image()

    async def _generate_clock_image(self) -> bytes:
        """Generate a simple clock display."""
        image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        
        try:
            # Try to use a built-in font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
        
        # Center the text
        bbox = draw.textbbox((0, 0), time_str, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (DISPLAY_WIDTH - text_width) // 2
        y = (DISPLAY_HEIGHT - text_height) // 2
        
        draw.text((x, y), time_str, fill=(226, 232, 255), font=font)
        
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    async def async_show_image(self, image_bytes: bytes) -> None:
        """Display an image on the BK Light."""
        try:
            image = Image.open(BytesIO(image_bytes))
            
            # Resize to display dimensions if needed
            if image.size != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
                image = image.resize(
                    (DISPLAY_WIDTH, DISPLAY_HEIGHT),
                    Image.Resampling.LANCZOS
                )
            
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Send to device
            success = await self._device.send_image(image)
            
            if success:
                self._current_image = image
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to send image to device")
                
        except Exception as err:
            _LOGGER.error("Error displaying image: %s", err)

    async def async_display_text(
        self,
        text: str,
        color: tuple[int, int, int] = (255, 0, 0),
        background: tuple[int, int, int] = (0, 0, 0),
        font_size: int = 12,
    ) -> None:
        """Display text on the BK Light."""
        image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=background)
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        
        # Center the text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (DISPLAY_WIDTH - text_width) // 2
        y = (DISPLAY_HEIGHT - text_height) // 2
        
        draw.text((x, y), text, fill=color, font=font)
        
        await self._device.send_image(image)
        self._current_image = image
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._device.is_connected

    async def async_update(self) -> None:
        """Update the entity."""
        # Check connection status
        if not self._device.is_connected:
            await self._device.connect()
