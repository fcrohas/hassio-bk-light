# Example Configuration

## UI Configuration (Recommended)

1. Navigate to **Configuration** → **Integrations** in Home Assistant
2. Click the **+ ADD INTEGRATION** button
3. Search for "BK Light ACT1026"
4. Enter the following information:
   - **Bluetooth MAC Address**: The Bluetooth MAC address of your BK Light display (e.g., `F0:27:3C:1A:8B:C3`)
   - **Device Name**: A friendly name for your display (e.g., "LED Matrix")
   - **Rotation**: Display rotation in degrees (0, 90, 180, 270)
   - **Brightness**: Display brightness from 0.1 to 1.0
5. Click **Submit**

## Services

The integration provides services to control the display:

### Display Image

```yaml
service: image.show
target:
  entity_id: image.bk_light_display
data:
  url: "https://example.com/image.png"
```

### Display Text (Custom Service)

```yaml
service: bk_light.display_text
target:
  entity_id: image.bk_light_display
data:
  text: "HELLO WORLD"
  color: [255, 0, 0]  # RGB
  background: [0, 0, 0]
  font_size: 12
```

## Automation Examples

### Display Clock

```yaml
automation:
  - alias: "Update Display Every Minute"
    trigger:
      platform: time_pattern
      minutes: "/1"
    action:
      service: bk_light.display_clock
      target:
        entity_id: image.bk_light_display
```

### Notification Display

```yaml
automation:
  - alias: "Show Doorbell Alert"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: "on"
    action:
      service: bk_light.display_text
      target:
        entity_id: image.bk_light_display
      data:
        text: "DOOR"
        color: [255, 255, 0]
        background: [0, 0, 0]
```

### Weather Display

```yaml
automation:
  - alias: "Display Temperature"
    trigger:
      platform: time_pattern
      minutes: "/5"
    action:
      service: bk_light.display_text
      target:
        entity_id: image.bk_light_display
      data:
        text: "{{ states('sensor.outdoor_temperature') }}°C"
        color: [100, 200, 255]
        background: [0, 0, 0]
```

### Display Camera Snapshot

```yaml
automation:
  - alias: "Show Camera on Motion"
    trigger:
      platform: state
      entity_id: binary_sensor.motion_sensor
      to: "on"
    action:
      service: camera.snapshot
      target:
        entity_id: camera.front_door
      data:
        filename: /tmp/snapshot.png
      enabled: true
    then:
      - delay: "00:00:01"
      - service: image.show
        target:
          entity_id: image.bk_light_display
        data:
          file_path: /tmp/snapshot.png
```

## Lovelace Card Example

```yaml
type: picture-entity
entity: image.bk_light_display
name: LED Matrix Display
show_state: false
show_name: true
```

## Script Examples

### Scrolling Text

```yaml
script:
  scroll_message:
    alias: "Scroll Message on Display"
    sequence:
      - service: bk_light.display_text
        target:
          entity_id: image.bk_light_display
        data:
          text: "{{ message }}"
          color: [255, 0, 0]
          scroll: true
          speed: 30
    variables:
      message: "WELCOME HOME"
```
