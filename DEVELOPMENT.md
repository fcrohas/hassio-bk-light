# Development Guide

## Setting up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/fcrohas/hassio-bk-light.git
cd hassio-bk-light
```

2. Install dependencies:
```bash
pip install bleak Pillow homeassistant
```

## Testing

### Manual Testing

1. Copy the `custom_components/bk_light` directory to your Home Assistant's `custom_components` directory:
```bash
cp -r custom_components/bk_light /config/custom_components/
```

2. Restart Home Assistant

3. Ensure Bluetooth is enabled on your Home Assistant host

4. Go to Configuration -> Integrations -> Add Integration -> Search for "BK Light ACT1026"

### Protocol Documentation

The BK Light ACT1026 uses Bluetooth Low Energy (BLE) with GATT/ATT protocol. It advertises as `LED_BLE_*`.

#### BLE UUIDs
- **Write Characteristic**: `0000fa02-0000-1000-8000-00805f9b34fb`
- **Notify Characteristic**: `0000fa03-0000-1000-8000-00805f9b34fb`

#### Connection Sequence

1. **Scan** for devices with name prefix `LED_BLE_`
2. **Connect** to device using BleakClient
3. **Enable notifications** on UUID_NOTIFY
4. **Perform handshake** before sending frames

#### Handshake Protocol

**Stage 1:**
```
TX: 08 00 01 80 0E 06 32 00
RX: 0C 00 01 80 81 06 32 00 00 01 00 01  (or ALT variant)
```

**Stage 2:**
```
TX: 04 00 05 80
RX: 08 00 05 80 0B 03 07 02  (may timeout, continue anyway)
```

**Stage 3 (Frame Send):**
```
TX: [Frame with PNG data]
RX: 05 00 02 00 03  (Frame ACK)
```

#### Frame Format

Frames contain PNG image data wrapped in a protocol envelope:

```python
frame_length = len(png_data) + 15  # Total frame size
frame = bytearray()
frame += frame_length.to_bytes(2, "little")
frame.append(0x02)
frame += b"\\x00\\x00"
frame += len(png_data).to_bytes(2, "little")
frame += b"\\x00\\x00"
frame += binascii.crc32(png_data).to_bytes(4, "little")
frame += b"\\x00\\x65"
frame += png_data
```

The PNG image must be:
- 32x32 pixels
- RGB format
- Can be adjusted for brightness/rotation before encoding

## Device Specifications

- **Display**: 32x32 RGB LED Matrix
- **Connection**: Bluetooth Low Energy 4.0+
- **MTU**: 512 bytes (negotiable)
- **Max Write**: Up to MTU size per GATT write
- **Supported Rotations**: 0°, 90°, 180°, 270°
- **Brightness**: 0.1 to 1.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with actual hardware
5. Submit a pull request

## Code Style

Follow PEP 8 guidelines and Home Assistant's coding standards:
- Use type hints
- Add docstrings to all functions
- Use async/await for I/O operations
- Log important events at appropriate levels

## Debugging

Enable debug logging in Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.bk_light: debug
    bleak: debug
```

## Publishing to HACS

1. Ensure all files are committed
2. Create a release tag:
```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

3. Submit to HACS:
   - Go to https://github.com/hacs/default
   - Fork the repository
   - Add your repository to `custom_components.json`
   - Submit a pull request

## Credits

Protocol reverse-engineered from:
- https://github.com/Pupariaa/Bk-Light-AppBypass
