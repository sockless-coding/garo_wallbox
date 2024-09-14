from typing import Callable, Awaitable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription


from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from .const import DOMAIN,COORDINATOR
from . import GaroConfigEntry

@dataclass(frozen=True, kw_only=True)
class GaroSwitchEntityDescription(SwitchEntityDescription):
    """Describes Garo Switch entity."""

    on_func: Callable[[], Awaitable]
    off_func: Callable[[], Awaitable]
    get_state: Callable[[], bool]

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        PanasonicSwitchEntity(coordinator, entry, description) for description in [
            GaroSwitchEntityDescription(
                key="charge_limit",
                translation_key="charge_limit",
                name="Charge Limiter",
                icon="mdi:ev-station",
                on_func=lambda: coordinator.async_enable_charge_limit(True),
                off_func=lambda: coordinator.async_enable_charge_limit(False),
                get_state=lambda: coordinator.config.charge_limit_enabled,
            ),
        ]])

class PanasonicSwitchEntity(GaroEntity, SwitchEntity):
    """Representation of a Garo switch."""
    entity_description: GaroSwitchEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSwitchEntityDescription, always_available: bool = False):
        """Initialize the Switch."""
        self.entity_description = description
        self._always_available = always_available
        super().__init__(coordinator, entry, description.key)

 
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_is_on = self.entity_description.get_state()
        

    async def async_turn_on(self, **kwargs):
        """Turn on the Switch."""
        await self.entity_description.on_func()
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the Switch."""
        await self.entity_description.off_func()
        self._attr_is_on = False
        self.async_write_ha_state()