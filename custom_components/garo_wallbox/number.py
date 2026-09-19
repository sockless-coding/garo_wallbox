from typing import Callable, Awaitable
from dataclasses import dataclass


from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from .garo import GaroStatus, const
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .base import GaroEntity, GaroMeterEntity, GaroMeter
from .const import (
    CONF_ALLOW_LOW_DLM_CURRENT,
    DEFAULT_ALLOW_LOW_DLM_CURRENT,
    DOMAIN,
    COORDINATOR,
)
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
    lb_min_current = (
        6
        if entry.options.get(
            CONF_ALLOW_LOW_DLM_CURRENT, DEFAULT_ALLOW_LOW_DLM_CURRENT
        )
        else 16
    )
    def load_balancing_enabled() -> bool:
        meter_coordinator = entry.runtime_data.meter_coordinator
        return (
            meter_coordinator is not None
            and meter_coordinator.has_lb_config
            and meter_coordinator.lb_config.enabled
        )

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
                is_available=lambda: coordinator.config.charge_limit_enabled and not load_balancing_enabled(),
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

        def add_lb_entity(
            meter: GaroMeter,
            key: str,
            name: str,
            icon: str,
            maximum: int,
            minimum: int,
            unit: str,
            get_value: Callable[[], int],
            set_value: Callable[[int], Awaitable],
            is_available: Callable[[], bool],
        ):
            entities.append(GaroLoadBalancingNumberEntity(
                meter_coordinator,
                coordinator,
                entry,
                GaroMeterNumberEntityDescription(
                    key=key,
                    translation_key=key,
                    name=name,
                    icon=icon,
                    native_max_value=maximum,
                    native_min_value=minimum,
                    native_step=1,
                    native_unit_of_measurement=unit,
                    mode=NumberMode.SLIDER,
                    get_value=lambda _: get_value(),
                    set_value=set_value,
                    is_available=is_available,
                ),
                meter,
            ))

        def add_lb_meter_entities(
            meter: GaroMeter,
            meter_number: int,
            get_fuse: Callable[[], int],
            set_fuse: Callable[[int], Awaitable],
        ):
            charger_count = (
                1 + len(coordinator.slaves) + (1 if configuration.has_twin else 0)
            )
            add_lb_entity(
                meter,
                f"load_balancing_current_{meter_number}",
                f"Meter {meter_number} Current Limit",
                "mdi:current-ac",
                charger_count * 32,
                lb_min_current,
                "A",
                get_fuse,
                set_fuse,
                lambda: True,
            )

        if meter_coordinator.has_lb_config:
            if meter_coordinator.has_central100_meter:
                add_lb_meter_entities(
                    meter_coordinator.central100_meter,
                    100,
                    lambda: meter_coordinator.lb_config.fuse,
                    meter_coordinator.async_set_lb_fuse,
                )
            if meter_coordinator.has_central101_meter:
                add_lb_meter_entities(
                    meter_coordinator.central101_meter,
                    101,
                    lambda: meter_coordinator.lb_config.fuse101,
                    meter_coordinator.async_set_lb_fuse101,
                )
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


class GaroLoadBalancingNumberEntity(GaroMeterNumberEntity):
    """Load-balancing number entity grouped under the master charger."""

    def __init__(
        self,
        coordinator: GaroMeterCoordinator,
        device_coordinator: GaroDeviceCoordinator,
        entry,
        description: GaroMeterNumberEntityDescription,
        meter: GaroMeter,
    ):
        super().__init__(coordinator, entry, description, meter)
        self._attr_unique_id = (
            f"{device_coordinator.device_id}-load_balancing-{description.key}"
        )
        self._attr_device_info = device_coordinator.device_info

    async def async_set_native_value(self, value: float) -> None:
        """Set a value and display the value read back from the charger."""
        await self.entity_description.set_value(int(value))
        self._async_update_attrs()
        self.async_write_ha_state()
