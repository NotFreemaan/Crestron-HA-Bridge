"""Config flow for Crestron Bridge integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CrestronBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Crestron Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"crestron_bridge_{port}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Crestron Bridge (Port {port})",
                data={CONF_PORT: port},
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
