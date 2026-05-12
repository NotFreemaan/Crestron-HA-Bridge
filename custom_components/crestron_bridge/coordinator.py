"""Coordinator for Crestron Bridge integration."""
import asyncio
import logging
from typing import Optional

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
    KEEPALIVE_INTERVAL,
    MESSAGE_TERMINATOR,
    NUM_AUDIO_ZONES,
    NUM_LIGHTS,
    NUM_VIDEO_ENDPOINTS,
    RESP_MUTE,
    RESP_STATUS,
    RESP_VOLSTATUS,
    RESP_VSTATUS,
)

_LOGGER = logging.getLogger(__name__)


class CrestronCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Crestron TCP server and state."""

    def __init__(self, hass: HomeAssistant, port: int) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.port = port

        self._server: Optional[asyncio.Server] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._read_task: Optional[asyncio.Task] = None
        self._client_address: Optional[str] = None

        self.data = {
            "lights": {i: False for i in range(1, NUM_LIGHTS + 1)},
            "video": {i: 0 for i in range(1, NUM_VIDEO_ENDPOINTS + 1)},
            "volume": {i: 0 for i in range(1, NUM_AUDIO_ZONES + 1)},
            "mute": {i: False for i in range(1, NUM_AUDIO_ZONES + 1)},
            "connected": False,
        }

    async def async_start(self) -> None:
        """Start the TCP server."""
        _LOGGER.info("Starting Crestron TCP server on port %s", self.port)
        try:
            self._server = await asyncio.start_server(
                self._handle_client, "0.0.0.0", self.port
            )
            _LOGGER.info("Waiting for Crestron to connect on port %s", self.port)
        except Exception as err:
            _LOGGER.error("Failed to start TCP server: %s", err)

    async def async_stop(self) -> None:
        """Stop the TCP server."""
        if self._read_task:
            self._read_task.cancel()
        await self._disconnect_client()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming Crestron connection."""
        addr = writer.get_extra_info("peername")
        self._client_address = f"{addr[0]}:{addr[1]}"
        _LOGGER.info("Crestron connected from %s", self._client_address)

        if self._connected:
            _LOGGER.warning("New connection received, dropping existing client")
            await self._disconnect_client()

        self._reader = reader
        self._writer = writer
        self._connected = True
        self.data["connected"] = True
        self.async_set_updated_data(self.data)

        self._read_task = asyncio.create_task(self._read_loop())
        await self._sync_all_states()

    async def _disconnect_client(self) -> None:
        """Disconnect the current client."""
        self._connected = False
        self.data["connected"] = False
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None
        self._client_address = None
        self.async_set_updated_data(self.data)

    async def _read_loop(self) -> None:
        """Read messages from the connected Crestron client."""
        buffer = ""
        while self._connected and self._reader:
            try:
                data = await self._reader.read(1024)
                if not data:
                    _LOGGER.warning("Crestron disconnected from %s", self._client_address)
                    await self._disconnect_client()
                    break

                buffer += data.decode("ascii", errors="ignore")
                while MESSAGE_TERMINATOR in buffer:
                    message, buffer = buffer.split(MESSAGE_TERMINATOR, 1)
                    message = message.strip()
                    if message:
                        await self._process_message(message)

            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Error reading from Crestron: %s", err)
                await self._disconnect_client()
                break

    async def _send_command(self, command: str) -> None:
        """Send a command to Crestron."""
        if not self._connected or not self._writer:
            _LOGGER.warning("Cannot send command, Crestron not connected")
            return
        try:
            self._writer.write(f"{command}{MESSAGE_TERMINATOR}".encode("ascii"))
            await self._writer.drain()
            _LOGGER.debug("Sent: %s", command)
        except Exception as err:
            _LOGGER.error("Error sending command: %s", err)
            await self._disconnect_client()

    async def _process_message(self, message: str) -> None:
        """Process an incoming message from Crestron."""
        _LOGGER.debug("Received: %s", message)
        parts = message.split(":")

        if len(parts) < 2:
            _LOGGER.warning("Invalid message: %s", message)
            return

        command = parts[0]

        try:
            if command == RESP_STATUS:
                light_num = int(parts[1])
                self.data["lights"][light_num] = int(parts[2]) == 1
                self.async_set_updated_data(self.data)

            elif command == CMD_LIGHT:
                light_num = int(parts[1])
                self.data["lights"][light_num] = parts[2].upper() == "ON"
                self.async_set_updated_data(self.data)

            elif command == RESP_VSTATUS:
                endpoint = int(parts[1])
                self.data["video"][endpoint] = int(parts[2])
                self.async_set_updated_data(self.data)

            elif command == CMD_VIDEO:
                endpoint = int(parts[1])
                self.data["video"][endpoint] = int(parts[2])
                self.async_set_updated_data(self.data)

            elif command == RESP_VOLSTATUS:
                zone = int(parts[1])
                self.data["volume"][zone] = self._crestron_to_ha_volume(int(parts[2]))
                self.async_set_updated_data(self.data)

            elif command == CMD_VOLUME:
                zone = int(parts[1])
                self.data["volume"][zone] = self._crestron_to_ha_volume(int(parts[2]))
                self.async_set_updated_data(self.data)

            elif command in (RESP_MUTE, CMD_MUTE):
                zone = int(parts[1])
                self.data["mute"][zone] = int(parts[2]) == 1
                self.async_set_updated_data(self.data)

        except (ValueError, IndexError) as err:
            _LOGGER.warning("Error parsing message '%s': %s", message, err)

    async def _sync_all_states(self) -> None:
        """Query all states from Crestron after connection."""
        _LOGGER.info("Syncing all states from Crestron")

        for i in range(1, NUM_LIGHTS + 1):
            await self._send_command(f"{CMD_QUERY}:{i}")
            await asyncio.sleep(0.05)

        for i in range(1, NUM_VIDEO_ENDPOINTS + 1):
            await self._send_command(f"{CMD_VQUERY}:{i}")
            await asyncio.sleep(0.05)

        for i in range(1, NUM_AUDIO_ZONES + 1):
            await self._send_command(f"{CMD_VOLQUERY}:{i}")
            await self._send_command(f"{CMD_MUTEQUERY}:{i}")
            await asyncio.sleep(0.05)

    def _crestron_to_ha_volume(self, crestron_level: int) -> int:
        crestron_level = max(0, min(CRESTRON_VOLUME_MAX, crestron_level))
        return round((crestron_level * HA_VOLUME_MAX) / CRESTRON_VOLUME_MAX)

    def _ha_to_crestron_volume(self, ha_level: int) -> int:
        ha_level = max(0, min(HA_VOLUME_MAX, ha_level))
        return round((ha_level * CRESTRON_VOLUME_MAX) / HA_VOLUME_MAX)

    async def set_light(self, light_num: int, state: bool) -> None:
        await self._send_command(f"{CMD_LIGHT}:{light_num}:{'ON' if state else 'OFF'}")

    async def query_light(self, light_num: int) -> None:
        await self._send_command(f"{CMD_QUERY}:{light_num}")

    async def set_video_source(self, endpoint: int, source: int) -> None:
        await self._send_command(f"{CMD_VIDEO}:{endpoint}:{source}")

    async def query_video(self, endpoint: int) -> None:
        await self._send_command(f"{CMD_VQUERY}:{endpoint}")

    async def set_volume(self, zone: int, ha_level: int) -> None:
        await self._send_command(f"{CMD_VOLUME}:{zone}:{self._ha_to_crestron_volume(ha_level)}")

    async def query_volume(self, zone: int) -> None:
        await self._send_command(f"{CMD_VOLQUERY}:{zone}")

    async def set_mute(self, zone: int, state: bool) -> None:
        await self._send_command(f"{CMD_MUTE}:{zone}:{1 if state else 0}")

    async def query_mute(self, zone: int) -> None:
        await self._send_command(f"{CMD_MUTEQUERY}:{zone}")

    async def reconnect(self) -> None:
        """Drop the current client, forcing Crestron to reconnect."""
        _LOGGER.info("Manual reconnection triggered")
        await self._disconnect_client()

    async def resync(self) -> None:
        """Manually trigger a full state resync."""
        _LOGGER.info("Manual resync triggered")
        await self._sync_all_states()
