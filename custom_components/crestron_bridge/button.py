"""Button platform for Crestron Bridge integration."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CrestronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crestron button entities."""
    coordinator: CrestronCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = [
        CrestronReconnectButton(coordinator),
        CrestronResyncButton(coordinator),
    ]

    async_add_entities(entities)


class CrestronReconnectButton(CoordinatorEntity, ButtonEntity):
    """Button to manually reconnect to Crestron."""

    def __init__(self, coordinator: CrestronCoordinator) -> None:
        """Initialize the reconnect button."""
        super().__init__(coordinator)
        self._attr_name = "Crestron Reconnect"
        self._attr_unique_id = f"crestron_bridge_{coordinator.host}_{coordinator.port}_reconnect"
        self._attr_icon = "mdi:connection"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Reconnect button pressed")
        await self.coordinator.reconnect()

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.host}_{self.coordinator.port}")},
            "name": f"Crestron Bridge ({self.coordinator.host})",
            "manufacturer": "Github@NotFreemaan",
            "model": "TCP Bridge",
        }


class CrestronResyncButton(CoordinatorEntity, ButtonEntity):
    """Button to manually resync states from Crestron."""

    def __init__(self, coordinator: CrestronCoordinator) -> None:
        """Initialize the resync button."""
        super().__init__(coordinator)
        self._attr_name = "Crestron Resync"
        self._attr_unique_id = f"crestron_bridge_{coordinator.host}_{coordinator.port}_resync"
        self._attr_icon = "mdi:sync"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Resync button pressed")
        await self.coordinator.resync()

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.host}_{self.coordinator.port}")},
            "name": f"Crestron Bridge ({self.coordinator.host})",
            "manufacturer": "Github@NotFreemaan",
            "model": "TCP Bridge",
        }
