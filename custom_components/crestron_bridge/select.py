"""Select platform for Crestron Bridge integration."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUM_VIDEO_ENDPOINTS, VIDEO_ENDPOINT_NAMES, VIDEO_SOURCE_NAMES
from .coordinator import CrestronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crestron select entities."""
    coordinator: CrestronCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities = []

    for i in range(1, NUM_VIDEO_ENDPOINTS + 1):
        endpoint_name = (
            VIDEO_ENDPOINT_NAMES[i - 1]
            if i - 1 < len(VIDEO_ENDPOINT_NAMES)
            else f"Endpoint {i}"
        )
        entities.append(
            CrestronVideoSourceSelect(coordinator, i, endpoint_name, VIDEO_SOURCE_NAMES)
        )

    async_add_entities(entities)


class CrestronVideoSourceSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Crestron video source selector."""

    def __init__(
        self,
        coordinator: CrestronCoordinator,
        endpoint: int,
        endpoint_name: str,
        source_names: list[str],
    ) -> None:
        """Initialize the video source selector."""
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._endpoint_name = endpoint_name
        self._source_names = source_names
        self._attr_name = f"Crestron {endpoint_name} Source"
        self._attr_unique_id = (
            f"crestron_bridge_{coordinator.port}_video_{endpoint}"
        )
        self._attr_options = source_names
        self._attr_icon = "mdi:video-input-hdmi"

    @property
    def current_option(self) -> str:
        """Return the current selected source."""
        source_num = self.coordinator.data["video"].get(self._endpoint, 0)
        if 0 <= source_num < len(self._source_names):
            return self._source_names[source_num]
        return self._source_names[0] if self._source_names else "Unknown"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data["connected"]

    async def async_select_option(self, option: str) -> None:
        """Change the selected source."""
        try:
            source_num = self._source_names.index(option)
            await self.coordinator.set_video_source(self._endpoint, source_num)
        except ValueError:
            _LOGGER.error("Invalid source option: %s", option)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"crestron_bridge_{self.coordinator.port}")},
            "name": f"Crestron Bridge (Port {self.coordinator.port})",
            "manufacturer": "Github@NotFreemaan",
            "model": "TCP Bridge",
        }
