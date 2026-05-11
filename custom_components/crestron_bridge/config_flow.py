"""Config flow for Crestron Bridge integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_AUDIO_ZONE_NAMES,
    CONF_NUM_AUDIO_ZONES,
    CONF_NUM_LIGHTS,
    CONF_NUM_VIDEO_ENDPOINTS,
    CONF_VIDEO_ENDPOINT_NAMES,
    CONF_VIDEO_SOURCE_NAMES,
    DEFAULT_AUDIO_ZONE_NAMES,
    DEFAULT_NUM_AUDIO_ZONES,
    DEFAULT_NUM_LIGHTS,
    DEFAULT_NUM_VIDEO_ENDPOINTS,
    DEFAULT_PORT,
    DEFAULT_VIDEO_ENDPOINT_NAMES,
    DEFAULT_VIDEO_SOURCE_NAMES,
    DEFAULT_VIDEO_SOURCES,
    DOMAIN,
    MAX_LIGHTS,
)

_LOGGER = logging.getLogger(__name__)


class CrestronBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Crestron Bridge."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._port: int = DEFAULT_PORT
        self._num_lights: int = DEFAULT_NUM_LIGHTS
        self._num_video_endpoints: int = DEFAULT_NUM_VIDEO_ENDPOINTS
        self._num_audio_zones: int = DEFAULT_NUM_AUDIO_ZONES

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store values for customization step
            self._port = user_input[CONF_PORT]
            self._num_lights = user_input[CONF_NUM_LIGHTS]
            self._num_video_endpoints = user_input[CONF_NUM_VIDEO_ENDPOINTS]
            self._num_audio_zones = user_input[CONF_NUM_AUDIO_ZONES]

            # Check for duplicates (only one instance per port)
            await self.async_set_unique_id(f"crestron_bridge_{self._port}")
            self._abort_if_unique_id_configured()

            # Proceed to customization step
            return await self.async_step_customize()

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_NUM_LIGHTS, default=DEFAULT_NUM_LIGHTS): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(
                    CONF_NUM_VIDEO_ENDPOINTS, default=DEFAULT_NUM_VIDEO_ENDPOINTS
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    CONF_NUM_AUDIO_ZONES, default=DEFAULT_NUM_AUDIO_ZONES
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_customize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the customization step for entity names."""
        if user_input is not None:
            # Parse the comma-separated lists
            video_source_names = [
                name.strip()
                for name in user_input.get(CONF_VIDEO_SOURCE_NAMES, "").split(",")
                if name.strip()
            ]
            video_endpoint_names = [
                name.strip()
                for name in user_input.get(CONF_VIDEO_ENDPOINT_NAMES, "").split(",")
                if name.strip()
            ]
            audio_zone_names = [
                name.strip()
                for name in user_input.get(CONF_AUDIO_ZONE_NAMES, "").split(",")
                if name.strip()
            ]

            # Use defaults if empty
            if not video_source_names:
                video_source_names = DEFAULT_VIDEO_SOURCE_NAMES[: DEFAULT_VIDEO_SOURCES]
            if not video_endpoint_names:
                video_endpoint_names = DEFAULT_VIDEO_ENDPOINT_NAMES[
                    : self._num_video_endpoints
                ]
            if not audio_zone_names:
                audio_zone_names = DEFAULT_AUDIO_ZONE_NAMES[: self._num_audio_zones]

            # Pad with defaults if needed
            while len(video_source_names) < DEFAULT_VIDEO_SOURCES:
                video_source_names.append(f"Source {len(video_source_names)}")
            while len(video_endpoint_names) < self._num_video_endpoints:
                video_endpoint_names.append(f"Endpoint {len(video_endpoint_names)}")
            while len(audio_zone_names) < self._num_audio_zones:
                audio_zone_names.append(f"Zone {len(audio_zone_names)}")

            # Create entry
            return self.async_create_entry(
                title=f"Crestron Bridge (Port {self._port})",
                data={
                    CONF_PORT: self._port,
                    CONF_NUM_LIGHTS: self._num_lights,
                    CONF_NUM_VIDEO_ENDPOINTS: self._num_video_endpoints,
                    CONF_NUM_AUDIO_ZONES: self._num_audio_zones,
                    CONF_VIDEO_SOURCE_NAMES: video_source_names,
                    CONF_VIDEO_ENDPOINT_NAMES: video_endpoint_names,
                    CONF_AUDIO_ZONE_NAMES: audio_zone_names,
                },
            )

        # Show customization form
        default_video_sources = ", ".join(
            DEFAULT_VIDEO_SOURCE_NAMES[: DEFAULT_VIDEO_SOURCES]
        )
        default_video_endpoints = ", ".join(
            DEFAULT_VIDEO_ENDPOINT_NAMES[: self._num_video_endpoints]
        )
        default_audio_zones = ", ".join(
            DEFAULT_AUDIO_ZONE_NAMES[: self._num_audio_zones]
        )

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_VIDEO_SOURCE_NAMES, default=default_video_sources
                ): cv.string,
                vol.Optional(
                    CONF_VIDEO_ENDPOINT_NAMES, default=default_video_endpoints
                ): cv.string,
                vol.Optional(
                    CONF_AUDIO_ZONE_NAMES, default=default_audio_zones
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="customize",
            data_schema=data_schema,
            description_placeholders={
                "video_sources_help": f"Enter {DEFAULT_VIDEO_SOURCES} source names separated by commas",
                "video_endpoints_help": f"Enter {self._num_video_endpoints} endpoint names separated by commas",
                "audio_zones_help": f"Enter {self._num_audio_zones} zone names separated by commas",
            },
        )
