import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription, ButtonDeviceClass

from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from . import GaroConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([GaroRestartButton(coordinator, entry)])


class GaroRestartButton(GaroEntity, ButtonEntity):
    """Restarts the wallbox (warm reset)."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: GaroDeviceCoordinator, entry) -> None:
        self.entity_description = ButtonEntityDescription(
            key="restart",
            translation_key="restart",
            name="Restart",
        )
        super().__init__(coordinator, entry, self.entity_description.key)

    def _async_update_attrs(self) -> None:
        """Buttons have no state to update."""

    async def async_press(self) -> None:
        """Restart the wallbox."""
        await self.coordinator.async_restart()
