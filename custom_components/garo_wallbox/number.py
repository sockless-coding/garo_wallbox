from typing import Callable, Awaitable
from dataclasses import dataclass


from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from .garo import GaroStatus, const
from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from .const import DOMAIN,COORDINATOR
from . import GaroConfigEntry

@dataclass(frozen=True, kw_only=True)
class GaroNumberEntityDescription(NumberEntityDescription):
    """Describes Garo Number entity."""
    get_value: Callable[[GaroStatus], int]
    set_value: Callable[[int], Awaitable]
    is_available: Callable[[], bool] | None = None

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    api_client = coordinator.api_client
    configuration = coordinator.config
    async_add_entities([
        GaroNumberEntity(coordinator, entry, description) for description in [
            GaroNumberEntityDescription(
                key="current_limit",
                translation_key="current_limit",
                name="Current Limit",
                icon="mdi:gauge",
                native_max_value=configuration.max_charge_current,
                native_min_value=6,
                native_step=1,
                native_unit_of_measurement="A",
                get_value=lambda status: status.current_limit,
                set_value=lambda value: api_client.async_set_current_limit(value),
                is_available=lambda: coordinator.config.charge_limit_enabled,
            ),
        ]])


class GaroNumberEntity(GaroEntity, NumberEntity):

    entity_description: GaroNumberEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroNumberEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""        
        return self.entity_description.is_available() and super().available if self.entity_description.is_available else super().available

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        value = int(value)
        await self.entity_description.set_value(value)
        self._attr_native_value = value
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self._attr_native_value = self.entity_description.get_value(self.coordinator.status)