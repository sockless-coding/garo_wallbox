from typing import Callable, Awaitable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription


from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .base import GaroEntity, GaroMeter, GaroMeterEntity
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
    entities:list[SwitchEntity] = [
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
        ]]
    if entry.runtime_data.meter_coordinator:
        meter_coordinator = entry.runtime_data.meter_coordinator
        def add_meter_entities(meter: GaroMeter):
            entities.extend(GaroMeterSwitchEntity(meter_coordinator, entry, description, meter) for description in [    
                GaroSwitchEntityDescription(
                    key="meter_calculate_power",
                    translation_key="meter_calculate_power",
                    name="Use calulated power values",
                    icon="mdi:calculator-variant",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    on_func=lambda: meter_coordinator.async_set_calculate_power(True),
                    off_func=lambda: meter_coordinator.async_set_calculate_power(False),
                    get_state=lambda: meter_coordinator.calculate_power,
                    )])
        if meter_coordinator.has_external_meter:
            add_meter_entities(meter_coordinator.external_meter)
        if meter_coordinator.has_central100_meter:
            add_meter_entities(meter_coordinator.central100_meter)
        if meter_coordinator.has_central101_meter:
            add_meter_entities(meter_coordinator.central101_meter)

    async_add_entities(entities)
    

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

class GaroMeterSwitchEntity(GaroMeterEntity, SwitchEntity):
    """Representation of a Garo switch."""
    entity_description: GaroSwitchEntityDescription

    def __init__(self, coordinator: GaroMeterCoordinator, entry, description: GaroSwitchEntityDescription, meter: GaroMeter):
        """Initialize the Switch."""
        self.entity_description = description
        super().__init__(coordinator, entry, description.key, meter)

 
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