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

            _LOGGER.info("Attempting to connect to device at %s...", self.address)
            
            # First, do a general scan to see what's available
            _LOGGER.debug("Starting BLE scan (15 seconds)...")
            try:
                devices = await BleakScanner.discover(timeout=15.0)
                _LOGGER.debug("Found %d BLE devices total", len(devices))
                
                # Log devices that might be BK Light displays
                for d in devices:
                    if d.name and any(prefix in d.name for prefix in ["LED_BLE", "BK_LIGHT", "BJ_LED"]):
                        _LOGGER.info(
                            "Found potential BK Light: %s at %s (RSSI: %s dBm)",
                            d.name,
                            d.address,
                            getattr(d, 'rssi', 'N/A')
                        )
                
                # Try to find our specific device
                device = next((d for d in devices if d.address.upper() == self.address.upper()), None)
                
                if device:
                    _LOGGER.info(
                        "Target device found: %s at %s (RSSI: %s dBm)",
                        getattr(device, 'name', 'Unknown'),
                        device.address,
                        getattr(device, 'rssi', 'N/A')
                    )
                else:
                    _LOGGER.warning(
                        "Device %s not found in scan. Found %d devices total. "
                        "Attempting direct connection...",
                        self.address,
                        len(devices)
                    )
                    # Try find_device_by_address as fallback
                    try:
                        device = await BleakScanner.find_device_by_address(
                            self.address, timeout=10.0, cached=False
                        )
                    except TypeError:
                        device = await BleakScanner.find_device_by_address(
                            self.address, timeout=10.0
                        )
            
            except Exception as scan_err:
                _LOGGER.warning("Error during discovery scan: %s. Trying direct connection...", scan_err)
                # Fallback to direct address lookup
                try:
                    device = await BleakScanner.find_device_by_address(
                        self.address, timeout=15.0, cached=False
                    )
                except TypeError:
                    device = await BleakScanner.find_device_by_address(
                        self.address, timeout=15.0
                    )
            
            if device is None:
                _LOGGER.error(
                    "Device %s not found after extensive scanning. "
                    "Please check:\n"
                    "  1. The device is powered on (display should be lit)\n"
                    "  2. The device is within 10 meters of the Bluetooth adapter\n"
                    "  3. The device is not connected to another device (phone/app)\n"
                    "  4. The MAC address is correct (use bk_light.scan_devices service)\n"
                    "  5. Bluetooth is enabled: sudo hciconfig hci0 up",
                    self.address
                )
                return False

            _LOGGER.info(
                "Attempting connection to %s (%s)...",
                device.address,
                getattr(device, 'name', 'Unknown')
            )
            
            self.client = BleakClient(device, timeout=20.0)
            await self.client.connect()
            
            _LOGGER.debug("Connected, starting notifications on UUID %s...", UUID_NOTIFY)
            await self.client.start_notify(UUID_NOTIFY, self._notification_handler)
            
            self._is_connected = True
            _LOGGER.info("Successfully connected to BK Light at %s", self.address)
            return True
            
        except BleakError as err:
            _LOGGER.error(
                "BLE error connecting to %s: %s. "
                "This may indicate the device is already connected elsewhere or out of range.",
                self.address,
                err
            )
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
