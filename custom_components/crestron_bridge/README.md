# Crestron Bridge - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Python-based Home Assistant custom integration that provides bidirectional TCP communication with Crestron control processors. This software-only solution eliminates the need for additional hardware bridges.

## Features

- **Direct TCP Connection** - Connects directly from Home Assistant to your Crestron processor
- **Bidirectional Communication** - Send commands to Crestron and receive feedback
- **Dynamic Entity Creation** - Creates entities based on your configuration
- **UI-Based Configuration** - No YAML editing required
- **Auto-Reconnect** - Automatically reconnects on connection loss
- **Real-Time Sync** - Syncs all entity states on connection

## Supported Entity Types

1. **Light/Switch Entities** (1-128 configurable)
   - Control Crestron lighting loads
   - Bidirectional state sync

2. **Video Source Selection** (up to 4 endpoints)
   - Select from 8 video sources per endpoint
   - Custom naming for sources and endpoints

3. **Volume Controls** (up to 4 zones)
   - 0-100% volume control
   - Automatic conversion from Crestron 0-65535 range

4. **Mute Switches** (up to 4 zones)
   - Mute/unmute audio zones
   - Visual indicators

5. **Connection Status Sensor**
   - Monitor connection state
   - Host and port information

6. **Diagnostic Buttons**
   - Manual reconnect trigger
   - State resync trigger

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/NotFreemaan/Crestron-HA-Private-Tester`
5. Select category: "Integration"
6. Click "Add"
7. Find "Crestron Bridge" in HACS and install it
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/crestron_bridge` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Crestron Bridge"
4. Enter your configuration:
   - **Crestron IP Address** (required)
   - **TCP Port** (default: 50001)
   - **Number of Lights** (1-128, default: 16)
   - **Number of Video Endpoints** (1-8, default: 4)
   - **Number of Audio Zones** (1-8, default: 4)
5. Customize entity names (optional):
   - Video source names (8 sources, comma-separated)
   - Video endpoint names (comma-separated)
   - Audio zone names (comma-separated)
6. Click **Submit**

## TCP Protocol Specification

All messages are ASCII text terminated with `\r\n`.

### Commands TO Crestron (sent by Home Assistant)

```
LIGHT:X:ON/OFF        - Control light X (X=1-128)
QUERY:X               - Request status of light X
VIDEO:E:S             - Route source S to endpoint E (E=1-4, S=0-8, 0=off)
VQUERY:E              - Request video routing status
VOLUME:Z:L            - Set volume zone Z to level L (Z=1-4, L=0-65535)
VOLQUERY:Z            - Request volume status
MUTE:Z:S              - Set mute zone Z to state S (Z=1-4, S=0/1)
MUTEQUERY:Z           - Request mute status
KEEPALIVE             - Connection keepalive (sent every 30s)
```

### Responses FROM Crestron

```
STATUS:X:Y            - Light X status (Y=0/1)
VSTATUS:E:S           - Video endpoint E routed to source S
VOLSTATUS:Z:L         - Volume zone Z at level L (0-65535)
MUTE:Z:S              - Mute zone Z state (0/1)
```

### Control Events FROM Crestron

```
LIGHT:X:ON/OFF        - Crestron keypad pressed (updates HA state)
VIDEO:E:S             - Crestron touchpanel changed source
VOLUME:Z:L            - Crestron adjusted volume
MUTE:Z:S              - Crestron toggled mute
```

## Crestron Side Implementation

You need a SIMPL+ or SIMPL# module on your Crestron processor that:

1. Opens a TCP server on the configured port (default 50001)
2. Accepts incoming connections from Home Assistant
3. Parses incoming commands and executes the corresponding actions
4. Sends status updates when states change
5. Responds to query commands with current states

### Example SIMPL+ Skeleton

```c
// TCP Server module
TCP_SERVER server;

// When command received
FUNCTION ProcessCommand(STRING cmd) {
    STRING parts[10];
    INTEGER num_parts;

    num_parts = ParseString(cmd, ":", parts);

    IF (parts[0] = "LIGHT") {
        // Handle light command
        // parts[1] = light number
        // parts[2] = ON/OFF
    }
    ELSE IF (parts[0] = "QUERY") {
        // Send STATUS response
    }
    // ... handle other commands
}

// When local state changes (keypad pressed, etc.)
FUNCTION SendLightUpdate(INTEGER light_num, INTEGER state) {
    STRING msg[50];

    IF (state = 1) {
        msg = "LIGHT:" + ITOA(light_num) + ":ON\r\n";
    } ELSE {
        msg = "LIGHT:" + ITOA(light_num) + ":OFF\r\n";
    }

    SocketSend(server.SocketID, msg);
}
```

## Volume Conversion

The integration automatically handles volume conversion:

- **Crestron**: 0-65535 (unsigned 16-bit analog value)
- **Home Assistant**: 0-100 (percentage)

Conversion formulas:
```python
ha_level = (crestron_level * 100) / 65535
crestron_level = (ha_level * 65535) / 100
```

## Connection Management

- **Auto-Reconnect**: Attempts to reconnect every 20 seconds on connection loss
- **Keepalive**: Sends keepalive message every 30 seconds
- **Auto-Sync**: Queries all entity states when connection is established
- **Manual Tools**: Use the Reconnect and Resync buttons for manual control

## Troubleshooting

### Integration won't connect

1. Verify the Crestron processor IP address and port
2. Ensure the Crestron program is running and listening on the specified port
3. Check firewall settings on both Home Assistant and Crestron
4. Verify network connectivity (ping test)

### Entities show "Unavailable"

- Check the Connection Status sensor
- If disconnected, use the Reconnect button
- Check Crestron processor logs for errors

### States not syncing

1. Use the Resync button to manually trigger state sync
2. Verify the Crestron program is sending status updates
3. Check Home Assistant logs for parsing errors

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.crestron_bridge: debug
```

## Development

### Project Structure

```
custom_components/crestron_bridge/
├── __init__.py              # Integration setup
├── manifest.json            # Integration metadata
├── config_flow.py           # UI configuration
├── const.py                 # Constants
├── coordinator.py           # TCP client & state management
├── switch.py                # Light and mute entities
├── select.py                # Video source entities
├── number.py                # Volume entities
├── button.py                # Diagnostic buttons
├── sensor.py                # Connection sensor
├── strings.json             # UI strings
└── translations/
    └── en.json              # English translations
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Credits

Developed as a software-only alternative to the ESPHome-based Crestron bridge.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
