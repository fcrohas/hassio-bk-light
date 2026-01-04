"""BK Light ACT1026 BLE Device Communication."""
from __future__ import annotations

import asyncio
import binascii
import logging
from io import BytesIO
from typing import Optional

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from PIL import Image, ImageEnhance

from .const import (
    ACK_STAGE_ONE,
    ACK_STAGE_ONE_ALT,
    ACK_STAGE_TWO,
    ACK_STAGE_TWO_ALT,
    ACK_STAGE_THREE,
    HANDSHAKE_FIRST,
    HANDSHAKE_SECOND,
    UUID_NOTIFY,
    UUID_WRITE,
)

_LOGGER = logging.getLogger(__name__)


class BKLightDevice:
    """Representation of a BK Light ACT1026 BLE device."""

    def __init__(
        self,
        address: str,
        rotation: int = 0,
        brightness: float = 0.85,
    ):
        """Initialize the device."""
        self.address = address
        self.rotation = rotation
        self._brightness = brightness
        self.client: Optional[BleakClient] = None
        self._ack_stage = 0
        self._ack_event = asyncio.Event()
        self._is_connected = False

    def _notification_handler(self, _sender: int, data: bytearray) -> None:
        """Handle BLE notifications."""
        payload = bytes(data)
        _LOGGER.debug("Received notification: %s", payload.hex())

        # Check ACK patterns
        if len(payload) >= 5:
            prefix = payload[:5]
            if prefix == ACK_STAGE_ONE[:5] or prefix == ACK_STAGE_ONE_ALT[:5]:
                self._ack_stage = 1
                _LOGGER.debug("ACK Stage 1 received")
            elif prefix == ACK_STAGE_TWO[:5] or prefix == ACK_STAGE_TWO_ALT[:5]:
                self._ack_stage = 2
                _LOGGER.debug("ACK Stage 2 received")
            elif prefix == ACK_STAGE_THREE[:5]:
                self._ack_stage = 3
                _LOGGER.debug("ACK Stage 3 received")
            self._ack_event.set()

    async def connect(self) -> bool:
        """Connect to the BLE device."""
        try:
            if self.client and self.client.is_connected:
                return True

            _LOGGER.debug("Scanning for device %s...", self.address)
            
            # Try to find device with different methods
            device = None
            try:
                # Try without cached first (preferred)
                device = await BleakScanner.find_device_by_address(
                    self.address, timeout=15.0, cached=False
                )
            except TypeError:
                # Fallback for older bleak versions without cached parameter
                device = await BleakScanner.find_device_by_address(
                    self.address, timeout=15.0
                )
            
            if device is None:
                # Try with cached=True as fallback
                _LOGGER.debug("Device not found, trying with cache...")
                try:
                    device = await BleakScanner.find_device_by_address(
                        self.address, timeout=15.0, cached=True
                    )
                except TypeError:
                    pass
            
            if device is None:
                _LOGGER.error(
                    "Device %s not found. Make sure it's powered on and in range. "
                    "The device should advertise as LED_BLE_*",
                    self.address
                )
                return False

            _LOGGER.debug("Device found: %s", device.name if hasattr(device, 'name') else 'Unknown')
            
            self.client = BleakClient(device)
            await self.client.connect()
            
            _LOGGER.debug("Connected, starting notifications...")
            await self.client.start_notify(UUID_NOTIFY, self._notification_handler)
            
            self._is_connected = True
            _LOGGER.info("Successfully connected to BK Light at %s", self.address)
            return True
            
        except BleakError as err:
            _LOGGER.error("BLE error connecting to %s: %s", self.address, err)
            self._is_connected = False
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
                self.client = None
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error connecting to %s: %s", self.address, err)
            self._is_connected = False
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
                self.client = None
            return False

    async def disconnect(self):
        """Disconnect from the device."""
        if self.client:
            try:
                if self.client.is_connected:
                    await self.client.stop_notify(UUID_NOTIFY)
                    await self.client.disconnect()
            except Exception as err:
                _LOGGER.error("Error disconnecting: %s", err)
            finally:
                self.client = None
                self._is_connected = False

    async def _wait_for_ack(self, expected_stage: int, timeout: float = 5.0) -> bool:
        """Wait for ACK stage."""
        try:
            await asyncio.wait_for(self._ack_event.wait(), timeout=timeout)
            self._ack_event.clear()
            return self._ack_stage == expected_stage
        except asyncio.TimeoutError:
            _LOGGER.warning("ACK timeout for stage %d", expected_stage)
            return False

    def _build_frame(self, png_bytes: bytes) -> bytes:
        """Build frame payload."""
        data_length = len(png_bytes)
        total_length = data_length + 15
        frame = bytearray()
        frame += total_length.to_bytes(2, "little")
        frame.append(0x02)
        frame += b"\\x00\\x00"
        frame += data_length.to_bytes(2, "little")
        frame += b"\\x00\\x00"
        frame += binascii.crc32(png_bytes).to_bytes(4, "little")
        frame += b"\\x00\\x65"
        frame += png_bytes
        return bytes(frame)

    def _adjust_image(self, image: Image.Image) -> bytes:
        """Adjust image brightness and rotation, return PNG bytes."""
        if self.rotation != 0:
            image = image.rotate(-self.rotation, expand=True)

        if self._brightness < 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self._brightness)

        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=False)
        return buffer.getvalue()

    async def send_image(self, image: Image.Image, delay: float = 0.2) -> bool:
        """Send an image to the display."""
        if not self.client or not self.client.is_connected:
            if not await self.connect():
                return False

        try:
            # Adjust image
            png_bytes = await asyncio.get_event_loop().run_in_executor(
                None, self._adjust_image, image
            )
            frame = self._build_frame(png_bytes)

            # Handshake stage 1
            self._ack_stage = 0
            self._ack_event.clear()
            await self.client.write_gatt_char(UUID_WRITE, HANDSHAKE_FIRST, response=False)
            if not await self._wait_for_ack(1):
                raise BleakError("Handshake stage 1 failed")
            await asyncio.sleep(delay)

            # Handshake stage 2
            self._ack_event.clear()
            await self.client.write_gatt_char(UUID_WRITE, HANDSHAKE_SECOND, response=False)
            # Stage 2 ACK may not always arrive, continue anyway
            try:
                await self._wait_for_ack(2, timeout=2.0)
            except asyncio.TimeoutError:
                _LOGGER.debug("Stage 2 ACK skipped")
            await asyncio.sleep(delay)

            # Send frame
            self._ack_event.clear()
            await self.client.write_gatt_char(UUID_WRITE, frame, response=True)
            if not await self._wait_for_ack(3):
                raise BleakError("Frame send failed")

            _LOGGER.debug("Image sent successfully")
            return True

        except Exception as err:
            _LOGGER.error("Error sending image: %s", err)
            return False

    @property
    def is_connected(self) -> bool:
        """Return True if device is connected."""
        return self._is_connected

    @property
    def brightness(self) -> float:
        """Return the brightness (0.0-1.0)."""
        return self._brightness

    def set_brightness(self, brightness: float):
        """Set brightness (0.0-1.0)."""
        self._brightness = max(0.1, min(1.0, brightness))
