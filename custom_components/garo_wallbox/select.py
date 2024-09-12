from typing import Callable, Awaitable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .garo import GaroStatus, const
from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from .const import DOMAIN,COORDINATOR

@dataclass(frozen=True, kw_only=True)
class GaroSelectEntityDescription(SelectEntityDescription):
    """Description of a select entity."""
    set_option: Callable[[str], Awaitable]
    get_current_option: Callable[[GaroStatus], str]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator:GaroDeviceCoordinator = hass.data[DOMAIN][COORDINATOR]
    api_client = coordinator.api_client
    async_add_entities([
        GaroSelectEntity(coordinator, entry, description) for description in [
            GaroSelectEntityDescription(
                key="sensor",
                translation_key="sensor",
                name=coordinator.main_charger_name,
                icon="mdi:ev-station",
                options=[opt.value for opt in const.Mode],
                set_option=lambda option: api_client.async_set_mode(option),
                get_current_option=lambda status: status.mode.value,
            ),
        ]])
       

class GaroSelectEntity(GaroEntity, SelectEntity):

    entity_description: GaroSelectEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSelectEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)

    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_option(option)
        self._attr_current_option = option
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self.current_option = self.entity_description.get_current_option(self.coordinator.status)