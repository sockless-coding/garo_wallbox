from typing import Callable, Awaitable
from dataclasses import dataclass


from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from .garo import GaroStatus, const
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .base import GaroEntity, GaroMeterEntity, GaroMeter
from .const import DOMAIN,COORDINATOR
from . import GaroConfigEntry

@dataclass(frozen=True, kw_only=True)
class GaroNumberEntityDescription(NumberEntityDescription):
    """Describes Garo Number entity."""
    get_value: Callable[[GaroStatus], int]
    set_value: Callable[[int], Awaitable]
    is_available: Callable[[], bool] | None = None

@dataclass(frozen=True, kw_only=True)
class GaroMeterNumberEntityDescription(NumberEntityDescription):
    """Describes Garo Number entity."""
    get_value: Callable[[GaroMeter], int]
    set_value: Callable[[int], Awaitable]
    is_available: Callable[[], bool] | None = None

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    configuration = coordinator.config
    entities:list[NumberEntity] =[
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
                set_value=lambda value: coordinator.async_set_current_limit(value),
                is_available=lambda: coordinator.config.charge_limit_enabled,
            ),
        ]]
    if entry.runtime_data.meter_coordinator:
        meter_coordinator = entry.runtime_data.meter_coordinator
        def add_meter_entities(meter: GaroMeter):
            entities.extend(GaroMeterNumberEntity(meter_coordinator, entry, description, meter) for description in [    
                GaroMeterNumberEntityDescription(
                    key="meter_mains_voltage",
                    translation_key="meter_mains_voltage",
                    name="Mains voltage",
                    icon="mdi:sine-wave",
                    native_max_value=280,
                    native_min_value=100,
                    native_step=1,
                    native_unit_of_measurement="V",
                    mode=NumberMode.BOX,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    get_value=lambda status: meter_coordinator.voltage,
                    set_value=lambda value: meter_coordinator.async_set_voltage(value),
                    is_available=lambda: True,
                    )])
        if meter_coordinator.has_external_meter:
            add_meter_entities(meter_coordinator.external_meter)
        if meter_coordinator.has_central100_meter:
            add_meter_entities(meter_coordinator.central100_meter)
        if meter_coordinator.has_central101_meter:
            add_meter_entities(meter_coordinator.central101_meter)

        def add_lb_fuse_entity(meter: GaroMeter, get_fuse: Callable[[], int], set_fuse: Callable[[int], Awaitable]):
            max_fuse = 2500 if configuration.lb_version2 else 63
            entities.append(GaroMeterNumberEntity(meter_coordinator, entry, GaroMeterNumberEntityDescription(
                key="lb_main_fuse",
                translation_key="lb_main_fuse",
                name="Main Fuse",
                icon="mdi:gauge-full",
                native_max_value=max_fuse,
                native_min_value=16,
                native_step=1,
                native_unit_of_measurement="A",
                mode=NumberMode.BOX,
                get_value=lambda status: get_fuse(),
                set_value=set_fuse,
                is_available=lambda: True,
            ), meter))
        if meter_coordinator.has_lb_config:
            if meter_coordinator.has_central100_meter:
                add_lb_fuse_entity(
                    meter_coordinator.central100_meter,
                    lambda: meter_coordinator.lb_config.fuse,
                    meter_coordinator.async_set_lb_fuse)
            if meter_coordinator.has_central101_meter:
                add_lb_fuse_entity(
                    meter_coordinator.central101_meter,
                    lambda: meter_coordinator.lb_config.fuse101,
                    meter_coordinator.async_set_lb_fuse101)
    async_add_entities(entities)


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

class GaroMeterNumberEntity(GaroMeterEntity, NumberEntity):

    entity_description: GaroMeterNumberEntityDescription

    def __init__(self, coordinator: GaroMeterCoordinator, entry, description: GaroMeterNumberEntityDescription, meter: GaroMeter):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key, meter)
    
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
        self._attr_native_value = self.entity_description.get_value(self._meter)