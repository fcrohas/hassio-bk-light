# Quick Troubleshooting Guide

## Device Not Found Error

### Immediate Actions (in order):

1. **Run the diagnostic tool:**
   ```bash
   python3 diagnostic.py
   ```
   This will show all BLE devices and identify any BK Light displays.

2. **Check device power:**
   - Is the display screen lit up (even if blank)?
   - Try unplugging and replugging the USB power

3. **Disconnect from other devices:**
   - Close the BK Light mobile app completely
   - Make sure no other device is connected via Bluetooth
   - The display can only connect to ONE device at a time

4. **Check Bluetooth adapter:**
   ```bash
   # Check if Bluetooth is up
   hciconfig
   
   # If it says DOWN, enable it:
   sudo hciconfig hci0 up
   
   # Try scanning manually:
   sudo hcitool lescan
   # Press Ctrl+C after a few seconds
   # Look for LED_BLE_* in the list
   ```

5. **Test with specific MAC address:**
   ```bash
   python3 diagnostic.py CC:42:DE:9A:B7:3B
   ```

### Common Causes

| Issue | Solution |
|-------|----------|
| Device already connected to phone | Close the BK Light app, force stop it, or reboot phone |
| Device out of range | Move closer (within 10 meters / 30 feet) |
| Bluetooth adapter issue | `sudo systemctl restart bluetooth` |
| Wrong MAC address | Use diagnostic tool to find correct address |
| Device in pairing mode | Power cycle the device |

### Inside Home Assistant

1. **Call scan service:**
   - Go to Developer Tools → Services
   - Service: `bk_light.scan_devices`
   - Click "Call Service"
   - Check logs for results

2. **Enable debug logging:**
   Edit `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.bk_light: debug
       bleak: debug
   ```
   Restart Home Assistant and check logs.

## Signal Strength

| RSSI Value | Quality | What to do |
|------------|---------|------------|
| -60 dBm or higher | Excellent | Perfect, no action needed |
| -61 to -75 dBm | Good | Should work fine |
| -76 to -85 dBm | Fair | Move closer if possible |
| Below -85 dBm | Weak | Too far, move much closer |

## Home Assistant OS Specific

If running Home Assistant OS:

```bash
# From SSH/Terminal add-on:
ha bluetooth info
ha bluetooth restart

# Check Bluetooth integration
# Go to Settings → Devices & Services
# Look for "Bluetooth" integration
```

## Permission Issues (Docker/Manual Install)

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth homeassistant

# Or run with sudo (not recommended for production)
sudo hass

# For Docker, ensure device is exposed:
# docker-compose.yml:
devices:
  - /dev/bus/usb:/dev/bus/usb
privileged: true
```

## Still Not Working?

1. Verify device works with official app first
2. Check if device firmware needs update
3. Try a different Bluetooth adapter
4. Run diagnostic with sudo: `sudo python3 diagnostic.py`
5. Post issue on GitHub with diagnostic output

## Quick Commands Reference

```bash
# Scan for BLE devices
sudo hcitool lescan

# Check Bluetooth status
hciconfig -a

# Enable Bluetooth
sudo hciconfig hci0 up

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check Bluetooth logs
journalctl -u bluetooth -f

# Run Home Assistant diagnostic
python3 diagnostic.py

# Test specific device
python3 diagnostic.py CC:42:DE:9A:B7:3B
```
