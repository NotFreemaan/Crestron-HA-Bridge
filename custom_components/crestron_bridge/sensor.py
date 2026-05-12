"""Sensor platform for Crestron Bridge integration."""
import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up Crestron sensor entities."""
    coordinator: CrestronCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = [CrestronConnectionSensor(coordinator)]

    async_add_entities(entities)


class CrestronConnectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor to monitor connection status."""

    def __init__(self, coordinator: CrestronCoordinator) -> None:
        """Initialize the connection sensor."""
        super().__init__(coordinator)
        self._attr_name = "Crestron Connection Status"
        self._attr_unique_id = f"crestron_bridge_{coordinator.host}_{coordinator.port}_connection"

    @property
    def native_value(self) -> str:
        """Return the connection status."""
        return "Connected" if self.coordinator.data["connected"] else "Disconnected"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return (
            "mdi:lan-connect"
            if self.coordinator.data["connected"]
            else "mdi:lan-disconnect"
        )

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "host": self.coordinator.host,
            "port": self.coordinator.port,
        }

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.host}_{self.coordinator.port}")},
            "name": f"Crestron Bridge ({self.coordinator.host})",
            "manufacturer": "Github@NotFreemaan",
            "model": "TCP Bridge",
        }
