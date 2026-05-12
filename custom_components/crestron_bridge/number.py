"""Number platform for Crestron Bridge integration."""
import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AUDIO_ZONE_NAMES, DOMAIN, NUM_AUDIO_ZONES
from .coordinator import CrestronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crestron number entities."""
    coordinator: CrestronCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = []

    for i in range(1, NUM_AUDIO_ZONES + 1):
        zone_name = AUDIO_ZONE_NAMES[i - 1] if i - 1 < len(AUDIO_ZONE_NAMES) else f"Zone {i}"
        entities.append(CrestronVolumeControl(coordinator, i, zone_name))

    async_add_entities(entities)


class CrestronVolumeControl(CoordinatorEntity, NumberEntity):
    """Representation of a Crestron volume control."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator: CrestronCoordinator, zone: int, zone_name: str
    ) -> None:
        """Initialize the volume control."""
        super().__init__(coordinator)
        self._zone = zone
        self._zone_name = zone_name
        self._attr_name = f"Crestron {zone_name} Volume"
        self._attr_unique_id = f"crestron_bridge_{coordinator.port}_volume_{zone}"
        self._attr_icon = "mdi:volume-high"

    @property
    def native_value(self) -> float:
        """Return the current volume."""
        return self.coordinator.data["volume"].get(self._zone, 0)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data["connected"]

    async def async_set_native_value(self, value: float) -> None:
        """Set the volume."""
        await self.coordinator.set_volume(self._zone, int(value))

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.port}")},
            "name": f"Crestron Bridge (Port {self.coordinator.port})",
            "manufacturer": "Github@NotFreemaan",
            "model": "TCP Bridge",
        }
