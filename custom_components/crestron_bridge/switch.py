"""Switch platform for Crestron Bridge integration."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AUDIO_ZONE_NAMES, DOMAIN, NUM_AUDIO_ZONES, NUM_LIGHTS
from .coordinator import CrestronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crestron switch entities."""
    coordinator: CrestronCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = []

    for i in range(1, NUM_LIGHTS + 1):
        entities.append(CrestronLightSwitch(coordinator, i))

    for i in range(1, NUM_AUDIO_ZONES + 1):
        zone_name = AUDIO_ZONE_NAMES[i - 1] if i - 1 < len(AUDIO_ZONE_NAMES) else f"Zone {i}"
        entities.append(CrestronMuteSwitch(coordinator, i, zone_name))

    async_add_entities(entities)


class CrestronLightSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Crestron light switch."""

    def __init__(self, coordinator: CrestronCoordinator, light_num: int) -> None:
        """Initialize the light switch."""
        super().__init__(coordinator)
        self._light_num = light_num
        self._attr_name = f"Crestron Light {light_num}"
        self._attr_unique_id = f"crestron_bridge_{coordinator.port}_light_{light_num}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data["lights"].get(self._light_num, False)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data["connected"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.set_light(self._light_num, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.set_light(self._light_num, False)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.port}")},
            "name": f"Crestron HA Bridge (Port {self.coordinator.port})",
            "manufacturer": "Github@NotFreemaan",
            "model": "Crestron HA Integration",
        }


class CrestronMuteSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Crestron mute switch."""

    def __init__(
        self, coordinator: CrestronCoordinator, zone: int, zone_name: str
    ) -> None:
        """Initialize the mute switch."""
        super().__init__(coordinator)
        self._zone = zone
        self._zone_name = zone_name
        self._attr_name = f"Crestron {zone_name} Mute"
        self._attr_unique_id = f"crestron_bridge_{coordinator.port}_mute_{zone}"

    @property
    def is_on(self) -> bool:
        """Return true if muted."""
        return self.coordinator.data["mute"].get(self._zone, False)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data["connected"]

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:volume-off" if self.is_on else "mdi:volume-high"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute the zone."""
        await self.coordinator.set_mute(self._zone, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute the zone."""
        await self.coordinator.set_mute(self._zone, False)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.port}")},
            "name": f"Crestron HA Bridge (Port {self.coordinator.port})",
            "manufacturer": "Github@NotFreemaan",
            "model": "Crestron HA Integration",
        }
