"""Coordinator for Crestron Bridge integration."""
import asyncio
import logging
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    AUDIO_ZONE_NAMES,
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
    RECONNECT_INTERVAL,
    RESP_MUTE,
    RESP_STATUS,
    RESP_VOLSTATUS,
    RESP_VSTATUS,
    VIDEO_ENDPOINT_NAMES,
    VIDEO_SOURCE_NAMES,
)

_LOGGER = logging.getLogger(__name__)


class CrestronCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Crestron TCP connection and state."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.host = host
        self.port = port

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._stop = False
        self._connection_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None

        self.data = {
            "lights": {i: False for i in range(1, NUM_LIGHTS + 1)},
            "video": {i: 0 for i in range(1, NUM_VIDEO_ENDPOINTS + 1)},
            "volume": {i: 0 for i in range(1, NUM_AUDIO_ZONES + 1)},
            "mute": {i: False for i in range(1, NUM_AUDIO_ZONES + 1)},
            "connected": False,
        }

    async def async_start(self) -> None:
        """Start the connection loop."""
        self._stop = False
        self._connection_task = asyncio.create_task(self._connection_loop())

    async def async_stop(self) -> None:
        """Stop the connection loop and disconnect."""
        self._stop = True
        if self._connection_task:
            self._connection_task.cancel()
        await self._disconnect()

    async def _connection_loop(self) -> None:
        """Continuously connect to Crestron, reconnecting on failure."""
        while not self._stop:
            try:
                _LOGGER.info("Connecting to Crestron at %s:%s", self.host, self.port)
                reader, writer = await asyncio.open_connection(self.host, self.port)
                self._reader = reader
                self._writer = writer
                self._connected = True
                self.data["connected"] = True
                self.async_set_updated_data(self.data)
                _LOGGER.info("Connected to Crestron at %s:%s", self.host, self.port)

                self._keepalive_task = asyncio.create_task(self._keepalive_loop())
                await self._sync_all_states()
                await self._read_loop()

            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Crestron connection error: %s", err)
            finally:
                if self._keepalive_task:
                    self._keepalive_task.cancel()
                    self._keepalive_task = None
                await self._disconnect()

            if not self._stop:
                _LOGGER.info("Reconnecting in %s seconds...", RECONNECT_INTERVAL)
                await asyncio.sleep(RECONNECT_INTERVAL)

    async def _disconnect(self) -> None:
        """Close the current connection."""
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
        self.async_set_updated_data(self.data)

    async def _read_loop(self) -> None:
        """Read and process messages from Crestron."""
        buffer = ""
        while self._connected and self._reader:
            try:
                data = await self._reader.read(1024)
                if not data:
                    _LOGGER.warning("Crestron disconnected")
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
                break

    async def _keepalive_loop(self) -> None:
        """Send periodic keepalive messages."""
        while self._connected:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            if self._connected:
                await self._send_command(CMD_KEEPALIVE)

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
            await self._disconnect()

    async def _process_message(self, message: str) -> None:
        """Process incoming message from Crestron."""
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
        """Query all states from Crestron."""
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
        """Manually trigger reconnection."""
        _LOGGER.info("Manual reconnection triggered")
        await self._disconnect()

    async def resync(self) -> None:
        """Manually trigger state resync."""
        _LOGGER.info("Manual resync triggered")
        await self._sync_all_states()
