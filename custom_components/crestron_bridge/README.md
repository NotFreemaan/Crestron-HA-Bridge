# Crestron Bridge - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

## Features

- **Direct TCP Connection** - Connects directly from Home Assistant to your Crestron processor
- **Bidirectional Communication** - Send commands to Crestron and receive feedback
- **Dynamic Entity Creation** - Creates entities based on your configuration
- **UI-Based Configuration** - No YAML editing required
- **Auto-Reconnect** - Automatically reconnects on connection loss (20s interval)
- **Real-Time Sync** - Syncs all entity states on connection

## Supported Entity Types

1. **Light/Switch Entities** (16 light entities)
   - Control Crestron lighting loads
   - Bidirectional state synchronization

2. **Video Source Selection** (4 video endpoints)
   - Select from 8 video sources per endpoint
   - Custom naming for sources and endpoints

3. **Volume Controls** (4 zones)
   - 0-100% volume control
   - Automatic conversion from Crestron 0-65535 range

4. **Mute Switches** (4 zones)
   - Mute/unmute audio zones
   - Visual indicators

5. **Connection Status Sensor**
   - Monitor connection state
   - Host and port information

6. **Diagnostic Buttons**
   - Manual reconnect trigger
   - State resync trigger

## Installation

### Via HACS

1. Open **HACS** in Home Assistant
2. Click the **three dots** menu (top right)
3. Select **Custom repositories**
4. Add repository:
   - **URL:** `https://github.com/NotFreemaan/Crestron-HA-Bridge`
   - **Category:** `Integration`
5. Click **Add**
6. Find **"Crestron Bridge"** in HACS
7. Click **Download**
8. **Restart Home Assistant**

## Configuration

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **"Crestron Bridge"**

### Step 2: Configure Connection

Enter your configuration:
- **Crestron IP Address** (required) - e.g., `192.168.1.100`
- **TCP Port** (default: `50001`)

### Step 3: Customize Names (Optional)

Customize entity names with comma-separated lists:
- **Video Source Names** - e.g., `Off, Apple TV, Xbox, PlayStation, Cable Box, Blu-ray, Chromecast, PC`
- **Video Endpoint Names** - e.g., `Living Room TV, Bedroom TV, Office Monitor, Kitchen Display`
- **Audio Zone Names** - e.g., `Living Room, Bedroom, Office, Kitchen`

### Step 4: Complete Setup

Click **Submit** and the integration will:
- Connect to your Crestron processor
- Create all configured entities
- Sync initial states

## Crestron Side Setup

### Installation Steps

1. Copy the `.usp` and `.ush` files to your SIMPL+ modules folder
2. Add the module to your SIMPL Windows program
3. Wire the signals as needed (lights, video, audio, etc.)
4. Configure the module with Home Assistant's IP address
5. Compile and load to your processor

## TCP Protocol

### Commands (Home Assistant → Crestron)

| Command | Format | Description | Example |
|---------|--------|-------------|---------|
| LIGHT | `LIGHT:X:ON/OFF` | Control light X | `LIGHT:5:ON\r\n` |
| QUERY | `QUERY:X` | Request light status | `QUERY:5\r\n` |
| VIDEO | `VIDEO:E:S` | Route source S to endpoint E | `VIDEO:1:3\r\n` |
| VQUERY | `VQUERY:E` | Request video routing | `VQUERY:1\r\n` |
| VOLUME | `VOLUME:Z:L` | Set volume (0-65535) | `VOLUME:1:32768\r\n` |
| VOLQUERY | `VOLQUERY:Z` | Request volume status | `VOLQUERY:1\r\n` |
| MUTE | `MUTE:Z:S` | Set mute state (0/1) | `MUTE:1:1\r\n` |
| MUTEQUERY | `MUTEQUERY:Z` | Request mute status | `MUTEQUERY:1\r\n` |
| KEEPALIVE | `KEEPALIVE` | Connection keepalive | `KEEPALIVE\r\n` |

### Responses (Crestron → Home Assistant)

| Response | Format | Description | Example |
|----------|--------|-------------|---------|
| STATUS | `STATUS:X:Y` | Light status (Y=0/1) | `STATUS:5:1\r\n` |
| VSTATUS | `VSTATUS:E:S` | Video routing status | `VSTATUS:1:3\r\n` |
| VOLSTATUS | `VOLSTATUS:Z:L` | Volume level (0-65535) | `VOLSTATUS:1:32768\r\n` |
| MUTE | `MUTE:Z:S` | Mute state (S=0/1) | `MUTE:1:1\r\n` |

### Control Events (Crestron → Home Assistant)

The Crestron processor can also send the same command format to update Home Assistant when local controls are used:

```
LIGHT:X:ON/OFF    - Light button pressed
VIDEO:E:S         - Endpoint changed source
VOLUME:Z:L        - Volume adjusted
MUTE:Z:S          - Mute pressed
```

### Volume Conversion

The integration automatically handles volume conversion:
- **Crestron:** 0-65535 (unsigned 16-bit)
- **Home Assistant:** 0-100 (percentage)

## Connection Management

- **Auto-Reconnect:** Attempts reconnection every 20 seconds on connection loss
- **Keepalive:** Sends keepalive message every 30 seconds
- **Auto-Sync:** Queries all entity states when connection is established
- **Manual Tools:** Use Reconnect and Resync buttons for manual control

## Entities Created

### Switches
- `switch.crestron_light_1` through `switch.crestron_light_16` 
- `switch.crestron_[zone_name]_mute` (per audio zone)

### Select Boxes
- `select.crestron_[endpoint_name]_source` (per video endpoint)

### Number Sliders
- `number.crestron_[zone_name]_volume` (per audio zone)

### Buttons
- `button.crestron_reconnect` - Manually reconnect to Crestron
- `button.crestron_resync` - Manually resync all states

### Sensors
- `sensor.crestron_connection_status` - Shows connection state

## SIMPL Debugger Example

```
00:00:06.062    1    module_connect
00:00:06.062    Connecting...    status$
00:00:06.062    Status: 1    status$
00:00:06.078    0    module_connect
00:00:06.094    Connected    status$
00:00:06.094    1    module_connected_fb
00:00:06.094    0    module_disconnected_fb
00:00:06.109    Connected    status$
00:00:06.937    QUERY:1    rx$_debug
00:00:06.937    STATUS:1:0\x0D\x0A    tx$_debug
00:00:06.984    QUERY:2    rx$_debug
00:00:06.984    STATUS:2:0\x0D\x0A    tx$_debug
00:00:07.031    QUERY:3    rx$_debug
00:00:07.031    STATUS:3:0\x0D\x0A    tx$_debug
00:00:07.078    QUERY:4    rx$_debug
00:00:07.094    STATUS:4:0\x0D\x0A    tx$_debug
00:00:07.140    QUERY:5    rx$_debug
00:00:07.140    STATUS:5:0\x0D\x0A    tx$_debug
00:00:07.187    QUERY:6    rx$_debug
00:00:07.187    STATUS:6:0\x0D\x0A    tx$_debug
00:00:07.234    QUERY:7    rx$_debug
00:00:07.234    STATUS:7:0\x0D\x0A    tx$_debug
00:00:07.281    QUERY:8    rx$_debug
00:00:07.297    STATUS:8:0\x0D\x0A    tx$_debug
00:00:07.344    QUERY:9    rx$_debug
00:00:07.344    STATUS:9:0\x0D\x0A    tx$_debug
00:00:07.390    QUERY:10    rx$_debug
00:00:07.390    STATUS:10:0\x0D\x0A    tx$_debug
00:00:07.437    QUERY:11    rx$_debug
00:00:07.453    STATUS:11:0\x0D\x0A    tx$_debug
00:00:07.500    QUERY:12    rx$_debug
00:00:07.500    STATUS:12:0\x0D\x0A    tx$_debug
00:00:07.547    QUERY:13    rx$_debug
00:00:07.547    STATUS:13:0\x0D\x0A    tx$_debug
00:00:07.594    QUERY:14    rx$_debug
00:00:07.594    STATUS:14:0\x0D\x0A    tx$_debug
00:00:07.640    QUERY:15    rx$_debug
00:00:07.656    STATUS:15:0\x0D\x0A    tx$_debug
00:00:08.765    QUERY:16    rx$_debug
00:00:08.781    STATUS:16:0\x0D\x0A    tx$_debug
00:00:08.828    VQUERY:1    rx$_debug
00:00:08.828    VSTATUS:1:0\x0D\x0A    tx$_debug
00:00:08.875    VQUERY:2    rx$_debug
00:00:08.875    VSTATUS:2:0\x0D\x0A    tx$_debug
00:00:08.922    VQUERY:3    rx$_debug
00:00:08.937    VSTATUS:3:0\x0D\x0A    tx$_debug
00:00:08.984    VQUERY:4    rx$_debug
00:00:08.984    VSTATUS:4:0\x0D\x0A    tx$_debug
00:00:09.031    VOLQUERY:1    rx$_debug
00:00:09.031    VOLSTATUS:1:0\x0D\x0A    tx$_debug
00:00:09.078    VOLQUERY:2    rx$_debug
00:00:09.078    VOLSTATUS:2:0\x0D\x0A    tx$_debug
00:00:09.125    VOLQUERY:3    rx$_debug
00:00:09.140    VOLSTATUS:3:0\x0D\x0A    tx$_debug
00:00:09.187    VOLQUERY:4    rx$_debug
00:00:09.187    VOLSTATUS:4:0\x0D\x0A    tx$_debug
00:00:10.265    MUTEQUERY:1    rx$_debug
00:00:10.281    MUTE:1:0\x0D\x0A    tx$_debug
00:00:10.328    MUTEQUERY:2    rx$_debug
00:00:10.328    MUTE:2:0\x0D\x0A    tx$_debug
00:00:10.375    MUTEQUERY:3    rx$_debug
00:00:10.375    MUTE:3:0\x0D\x0A    tx$_debug
00:00:10.422    MUTEQUERY:4    rx$_debug
00:00:10.437    MUTE:4:0\x0D\x0A    tx$_debug
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
