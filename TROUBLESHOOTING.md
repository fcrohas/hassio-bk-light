# Troubleshooting BK Light ACT1026 Connection Issues

## Common Issues and Solutions

### 1. Device Not Found During Setup

**Symptoms:**
- Error: "Failed to connect to device"
- Error: "Device not found"

**Solutions:**

1. **Verify the device is powered on**
   - Check that the BK Light display shows something (even a blank screen means it's on)
   - Try power cycling the device

2. **Check Bluetooth MAC Address**
   - Make sure you're using the correct format: `XX:XX:XX:XX:XX:XX`
   - The address should be in uppercase
   - You can find the MAC address using the scan service (see below)

3. **Ensure Bluetooth is enabled on your Home Assistant host**
   ```bash
   # Check Bluetooth status
   sudo hciconfig
   
   # If it shows "DOWN", enable it
   sudo hciconfig hci0 up
   
   # Check if Bluetooth service is running
   sudo systemctl status bluetooth
   ```

4. **Check Bluetooth range**
   - The device should be within 10 meters (30 feet) of your Home Assistant host
   - Avoid obstacles like walls or metal objects between them

5. **Disconnect from other devices**
   - If the BK Light is paired/connected to a phone or other device, disconnect it first
   - The device can only maintain one active BLE connection at a time

### 2. Using the Scan Service

The integration provides a diagnostic service to scan for BLE devices:

1. Go to **Developer Tools** → **Services**
2. Select service: `bk_light.scan_devices`
3. Click **Call Service**
4. Check the Home Assistant logs for results:
   - Go to **Settings** → **System** → **Logs**
   - Look for entries from `custom_components.bk_light`

Example log output:
```
2026-01-05 00:18:24 INFO (MainThread) [custom_components.bk_light.services] Found 1 BK Light devices:
2026-01-05 00:18:24 INFO (MainThread) [custom_components.bk_light.services]   - LED_BLE_XXXX at CC:42:DE:9A:B7:3B (RSSI: -45 dBm)
```

### 3. Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.bk_light: debug
    bleak: debug
```

Then restart Home Assistant and check the logs for detailed information.

### 4. Bluetooth Adapter Issues

**Check your Bluetooth adapter:**

```bash
# List Bluetooth adapters
hciconfig -a

# Scan for BLE devices
sudo hcitool lescan
# Press Ctrl+C to stop

# Alternative using bluetoothctl
bluetoothctl
[bluetooth]# scan on
# Wait a few seconds, look for LED_BLE_* devices
[bluetooth]# scan off
[bluetooth]# exit
```

**If you see permission errors:**

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth homeassistant

# Or if running in Docker, make sure Bluetooth device is accessible
# Add to docker-compose.yml:
devices:
  - /dev/bus/usb:/dev/bus/usb
privileged: true
```

### 5. Home Assistant OS / Supervised

If running Home Assistant OS or Supervised:

1. **Check Bluetooth integration is enabled**
   - Go to **Settings** → **Devices & Services** → **Integrations**
   - Look for "Bluetooth" integration
   - If not present, your system may not have Bluetooth support

2. **Check Bluetooth adapter detection**
   - Go to **Settings** → **System** → **Hardware**
   - Look for Bluetooth adapter in the list

3. **Restart Bluetooth**
   ```bash
   # From SSH or console
   ha bluetooth restart
   ```

### 6. Multiple Bluetooth Adapters

If you have multiple Bluetooth adapters, you may need to specify which one to use:

1. Find your adapters:
   ```bash
   hciconfig
   ```

2. Disable unused adapters:
   ```bash
   sudo hciconfig hci1 down  # Replace hci1 with the adapter you don't want
   ```

### 7. Interference Issues

Bluetooth operates on 2.4 GHz which can interfere with WiFi:

- Try moving the device or Bluetooth adapter away from WiFi routers
- Change WiFi channel to reduce interference
- Use 5 GHz WiFi if possible

### 8. Firmware/Software Issues

1. **Update Home Assistant:**
   - Go to **Settings** → **System** → **Updates**

2. **Update Bleak library:**
   ```bash
   pip install --upgrade bleak
   ```

3. **Check BK Light firmware:**
   - Use the official BK Light app to check for firmware updates

### 9. Still Not Working?

If none of the above helps:

1. **Collect diagnostic information:**
   - Home Assistant version
   - Bluetooth adapter model
   - Output of `hciconfig -a`
   - Output of `sudo hcitool lescan` showing the device
   - Home Assistant logs with debug enabled

2. **Open an issue** on GitHub:
   - https://github.com/fcrohas/hassio-bk-light/issues
   - Include all diagnostic information

### 10. Known Limitations

- **Single connection:** The BK Light can only connect to one device at a time
- **Range:** Typical BLE range is 10-30 meters in open space
- **Compatibility:** Requires BLE 4.0+ adapter with GATT support
- **MTU size:** Requires MTU negotiation support (usually 512 bytes)

## Connection Test Commands

Test if you can see the device from command line:

```bash
# Using hcitool (older method)
sudo hcitool lescan | grep LED_BLE

# Using bluetoothctl (recommended)
bluetoothctl
[bluetooth]# scan on
# Look for LED_BLE_* devices
[bluetooth]# devices
# Note the MAC address
[bluetooth]# scan off
[bluetooth]# exit

# Test connection (replace MAC address)
sudo gatttool -b CC:42:DE:9A:B7:3B -I
[CC:42:DE:9A:B7:3B][LE]> connect
# Should see "Connection successful"
[CC:42:DE:9A:B7:3B][LE]> exit
```

If these commands work but Home Assistant doesn't connect, there may be a permission or library issue.
