"""The Crestron Bridge integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NUM_AUDIO_ZONES,
    CONF_NUM_LIGHTS,
    CONF_NUM_VIDEO_ENDPOINTS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CrestronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Crestron Bridge from a config entry."""
    port = entry.data[CONF_PORT]
    num_lights = entry.data[CONF_NUM_LIGHTS]
    num_video_endpoints = entry.data[CONF_NUM_VIDEO_ENDPOINTS]
    num_audio_zones = entry.data[CONF_NUM_AUDIO_ZONES]

    coordinator = CrestronCoordinator(
        hass, port, num_lights, num_video_endpoints, num_audio_zones
    )

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }

    # Start the coordinator
    await coordinator.async_start()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop coordinator
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.async_stop()

        # Remove entry
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
