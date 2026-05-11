"""Coordinator for Crestron Bridge integration."""
import asyncio
import logging
from typing import Any, Callable, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CMD_KEEPALIVE,
    CMD_LIGHT,
    CMD_MUTE,
    CMD_MUTEQUERY,
    CMD_QUERY,
    CMD_VIDEO,
    CMD_VOLQUERY,
    CMD_VOLUME,
    CMD_VQUERY,
    CRESTRON_VOLUME_MAX,
    DOMAIN,
    HA_VOLUME_MAX,
    MESSAGE_TERMINATOR,
    RESP_MUTE,
    RESP_STATUS,
    RESP_VOLSTATUS,
    RESP_VSTATUS,
)

_LOGGER = logging.getLogger(__name__)


class CrestronCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Crestron TCP server and state."""

    def __init__(
        self,
        hass: HomeAssistant,
        port: int,
        num_lights: int,
        num_video_endpoints: int,
        num_audio_zones: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.port = port
        self.num_lights = num_lights
        self.num_video_endpoints = num_video_endpoints
        self.num_audio_zones = num_audio_zones

        self._server: Optional[asyncio.Server] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._read_task: Optional[asyncio.Task] = None
        self._client_address: Optional[str] = None

        # State storage
        self.data = {
            "lights": {},  # {light_num: bool}
            "video": {},  # {endpoint: source}
            "volume": {},  # {zone: level (0-100)}
            "mute": {},  # {zone: bool}
            "connected": False,
        }

        # Initialize default states
        for i in range(1, num_lights + 1):
            self.data["lights"][i] = False
        for i in range(1, num_video_endpoints + 1):
            self.data["video"][i] = 0
        for i in range(1, num_audio_zones + 1):
            self.data["volume"][i] = 0
            self.data["mute"][i] = False

    async def async_start(self) -> None:
        """Start the TCP server."""
        _LOGGER.info("Starting Crestron TCP server on port %s", self.port)
        try:
            self._server = await asyncio.start_server(
                self._handle_client, "0.0.0.0", self.port
            )
            _LOGGER.info("TCP server listening on port %s", self.port)
            _LOGGER.info("Waiting for Crestron to connect...")
        except Exception as err:
            _LOGGER.error("Failed to start TCP server: %s", err)

    async def async_stop(self) -> None:
        """Stop the TCP server."""
        _LOGGER.info("Stopping Crestron TCP server")
        if self._read_task:
            self._read_task.cancel()
        await self._disconnect_client()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming client connection."""
        addr = writer.get_extra_info("peername")
        self._client_address = f"{addr[0]}:{addr[1]}"
        _LOGGER.info("Crestron connected from %s", self._client_address)

        # If we already have a client, disconnect it
        if self._connected:
            _LOGGER.warning("New connection, disconnecting existing client")
            await self._disconnect_client()

        self._reader = reader
        self._writer = writer
        self._connected = True
        self.data["connected"] = True
        self.async_set_updated_data(self.data)

        # Start reading messages
        self._read_task = asyncio.create_task(self._read_loop())

        # Sync all states
        await self._sync_all_states()

    async def _disconnect_client(self) -> None:
        """Disconnect current client."""
        self._connected = False
        self.data["connected"] = False
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as err:
                _LOGGER.debug("Error closing client connection: %s", err)
        self._reader = None
        self._writer = None
        self._client_address = None
        self.async_set_updated_data(self.data)

    async def _read_loop(self) -> None:
        """Read messages from Crestron client."""
        buffer = ""
        while self._connected and self._reader:
            try:
                data = await self._reader.read(1024)
                if not data:
                    _LOGGER.warning("Crestron disconnected from %s", self._client_address)
                    await self._disconnect_client()
                    _LOGGER.info("Waiting for Crestron to reconnect...")
                    break

                buffer += data.decode("ascii", errors="ignore")

                # Process complete messages
                while MESSAGE_TERMINATOR in buffer:
                    message, buffer = buffer.split(MESSAGE_TERMINATOR, 1)
                    message = message.strip()
                    if message:
                        await self._process_message(message)

            except Exception as err:
                _LOGGER.error("Error reading from Crestron: %s", err)
                await self._disconnect_client()
                _LOGGER.info("Waiting for Crestron to reconnect...")
                break

    async def _send_command(self, command: str) -> None:
        """Send a command to Crestron."""
        if not self._connected or not self._writer:
            _LOGGER.warning("Cannot send command, Crestron not connected")
            return

        try:
            message = f"{command}{MESSAGE_TERMINATOR}"
            self._writer.write(message.encode("ascii"))
            await self._writer.drain()
            _LOGGER.debug("Sent command: %s", command)
        except Exception as err:
            _LOGGER.error("Error sending command: %s", err)
            await self._disconnect_client()

    async def _process_message(self, message: str) -> None:
        """Process incoming message from Crestron."""
        _LOGGER.debug("Received message: %s", message)
        parts = message.split(":")

        if len(parts) < 2:
            _LOGGER.warning("Invalid message format: %s", message)
            return

        command = parts[0]

        try:
            if command == RESP_STATUS:
                # STATUS:X:Y - Light X status
                light_num = int(parts[1])
                state = int(parts[2]) == 1
                self.data["lights"][light_num] = state
                self.async_set_updated_data(self.data)

            elif command == CMD_LIGHT:
                # LIGHT:X:ON/OFF - Crestron control event
                light_num = int(parts[1])
                state = parts[2].upper() == "ON"
                self.data["lights"][light_num] = state
                self.async_set_updated_data(self.data)

            elif command == RESP_VSTATUS:
                # VSTATUS:E:S - Video endpoint E routed to source S
                endpoint = int(parts[1])
                source = int(parts[2])
                self.data["video"][endpoint] = source
                self.async_set_updated_data(self.data)

            elif command == CMD_VIDEO:
                # VIDEO:E:S - Crestron control event
                endpoint = int(parts[1])
                source = int(parts[2])
                self.data["video"][endpoint] = source
                self.async_set_updated_data(self.data)

            elif command == RESP_VOLSTATUS:
                # VOLSTATUS:Z:L - Volume zone Z at level L (0-65535)
                zone = int(parts[1])
                crestron_level = int(parts[2])
                ha_level = self._crestron_to_ha_volume(crestron_level)
                self.data["volume"][zone] = ha_level
                self.async_set_updated_data(self.data)

            elif command == CMD_VOLUME:
                # VOLUME:Z:L - Crestron control event
                zone = int(parts[1])
                crestron_level = int(parts[2])
                ha_level = self._crestron_to_ha_volume(crestron_level)
                self.data["volume"][zone] = ha_level
                self.async_set_updated_data(self.data)

            elif command == RESP_MUTE or command == CMD_MUTE:
                # MUTE:Z:S - Mute zone Z state
                zone = int(parts[1])
                state = int(parts[2]) == 1
                self.data["mute"][zone] = state
                self.async_set_updated_data(self.data)

        except (ValueError, IndexError) as err:
            _LOGGER.warning("Error parsing message '%s': %s", message, err)

    async def _sync_all_states(self) -> None:
        """Query all states from Crestron."""
        _LOGGER.info("Syncing all states from Crestron")

        # Query all lights
        for i in range(1, self.num_lights + 1):
            await self._send_command(f"{CMD_QUERY}:{i}")
            await asyncio.sleep(0.05)  # Small delay to avoid overwhelming

        # Query all video endpoints
        for i in range(1, self.num_video_endpoints + 1):
            await self._send_command(f"{CMD_VQUERY}:{i}")
            await asyncio.sleep(0.05)

        # Query all audio zones
        for i in range(1, self.num_audio_zones + 1):
            await self._send_command(f"{CMD_VOLQUERY}:{i}")
            await self._send_command(f"{CMD_MUTEQUERY}:{i}")
            await asyncio.sleep(0.05)

    def _crestron_to_ha_volume(self, crestron_level: int) -> int:
        """Convert Crestron volume (0-65535) to HA (0-100)."""
        # Clamp to valid range (handle potential negative values from overflow)
        crestron_level = max(0, min(CRESTRON_VOLUME_MAX, crestron_level))
        return round((crestron_level * HA_VOLUME_MAX) / CRESTRON_VOLUME_MAX)

    def _ha_to_crestron_volume(self, ha_level: int) -> int:
        """Convert HA volume (0-100) to Crestron (0-65535)."""
        # Clamp to valid range
        ha_level = max(0, min(HA_VOLUME_MAX, ha_level))
        return round((ha_level * CRESTRON_VOLUME_MAX) / HA_VOLUME_MAX)

    # Public methods for entity control

    async def set_light(self, light_num: int, state: bool) -> None:
        """Turn light on or off."""
        command = f"{CMD_LIGHT}:{light_num}:{'ON' if state else 'OFF'}"
        await self._send_command(command)

    async def query_light(self, light_num: int) -> None:
        """Query light status."""
        await self._send_command(f"{CMD_QUERY}:{light_num}")

    async def set_video_source(self, endpoint: int, source: int) -> None:
        """Set video source for endpoint."""
        await self._send_command(f"{CMD_VIDEO}:{endpoint}:{source}")

    async def query_video(self, endpoint: int) -> None:
        """Query video routing status."""
        await self._send_command(f"{CMD_VQUERY}:{endpoint}")

    async def set_volume(self, zone: int, ha_level: int) -> None:
        """Set volume level."""
        crestron_level = self._ha_to_crestron_volume(ha_level)
        await self._send_command(f"{CMD_VOLUME}:{zone}:{crestron_level}")

    async def query_volume(self, zone: int) -> None:
        """Query volume status."""
        await self._send_command(f"{CMD_VOLQUERY}:{zone}")

    async def set_mute(self, zone: int, state: bool) -> None:
        """Set mute state."""
        await self._send_command(f"{CMD_MUTE}:{zone}:{1 if state else 0}")

    async def query_mute(self, zone: int) -> None:
        """Query mute status."""
        await self._send_command(f"{CMD_MUTEQUERY}:{zone}")

    async def reconnect(self) -> None:
        """Manually trigger reconnection."""
        _LOGGER.info("Manual reconnection triggered - disconnecting current client")
        await self._disconnect_client()
        _LOGGER.info("Waiting for Crestron to reconnect...")

    async def resync(self) -> None:
        """Manually trigger state resync."""
        _LOGGER.info("Manual resync triggered")
        await self._sync_all_states()
