# BK Light ACT1026 Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Custom Home Assistant integration for the BK Light ACT1026 - a 32x32 RGB LED matrix display that connects via Bluetooth Low Energy (BLE).

## Features

- Display clock (12h/24h format)
- Display custom text with scrolling effects
- Show images and animations
- Multiple fonts and colors
- Brightness control
- Rotation and mirror effects
- Multi-panel support for larger displays

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/fcrohas/hassio-bk-light`
6. Select category "Integration"
7. Click "Add"
8. Find "BK Light ACT1026" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/bk_light` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)

1. **Ensure Bluetooth is enabled** on your Home Assistant installation
2. Power on your BK Light ACT1026 display
3. Go to Configuration -> Integrations
4. Click the "+ ADD INTEGRATION" button
5. Search for "BK Light ACT1026"
6. The device should be auto-discovered. If not, enter the Bluetooth MAC address manually
7. Click "Submit"

### YAML Configuration (Legacy)

Add the following to your `configuration.yaml`:

```yaml
image:
  - platform: bk_light
    address: "F0:27:3C:1A:8B:C3"  # Bluetooth MAC address
    name: "LED Matrix Display"
```

## Device Information

The BK Light ACT1026 is a 32x32 RGB LED matrix display that connects via Bluetooth Low Energy (BLE). The device advertises as `LED_BLE_*` and uses GATT/ATT protocol for communication.

### Supported Features

- Clock display (12h/24h format with dot flashing)
- Text display with scrolling marquee
- Image display (PNG format)
- Brightness adjustment (0.1 - 1.0)
- Rotation (0°, 90°, 180°, 270°)
- Multiple font support
- Multi-panel tiling

## Troubleshooting

### Device Not Found

- Ensure Bluetooth is enabled on your Home Assistant host
- Check that the BK Light display is powered on
- Verify the device is advertising (should show as `LED_BLE_*`)
- Ensure you're within Bluetooth range (typically 10m/30ft)

### Connection Issues

- Try power cycling the BK Light display
- Check Bluetooth adapter status: `hciconfig` or `bluetoothctl`
- Ensure no other devices are connected to the display
- Verify BLE 4.0+ support on your Bluetooth adapter

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by BK Light.
