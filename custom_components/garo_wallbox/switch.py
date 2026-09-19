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
    is_available: Callable[[], bool] | None = None

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    def load_balancing_enabled() -> bool:
        meter_coordinator = entry.runtime_data.meter_coordinator
        return (
            meter_coordinator is not None
            and meter_coordinator.has_lb_config
            and meter_coordinator.lb_config.enabled
        )

    entities:list[SwitchEntity] = [
        GaroSwitchEntity(coordinator, entry, description) for description in [
            GaroSwitchEntityDescription(
                key="charge_limit",
                translation_key="charge_limit",
                name="Charge Limiter",
                icon="mdi:ev-station",
                on_func=lambda: coordinator.async_enable_charge_limit(True),
                off_func=lambda: coordinator.async_enable_charge_limit(False),
                get_state=lambda: coordinator.config.charge_limit_enabled,
                is_available=lambda: not load_balancing_enabled(),
            ),
        ]]
    if coordinator.config.rfid_reader_present:
        entities.append(GaroSwitchEntity(coordinator, entry, GaroSwitchEntityDescription(
            key="rfid_enabled",
            translation_key="rfid_enabled",
            name="RFID Authorization",
            icon="mdi:card-account-details-outline",
            on_func=lambda: coordinator.async_set_rfid_mode(True),
            off_func=lambda: coordinator.async_set_rfid_mode(False),
            get_state=lambda: coordinator.config.rfid_enabled,
        )))
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

        def add_load_balancing_switch(
            meter: GaroMeter,
            key: str,
            name: str,
            icon: str,
            on_func: Callable[[], Awaitable],
            off_func: Callable[[], Awaitable],
            get_state: Callable[[], bool],
        ):
            entities.append(GaroLoadBalancingSwitchEntity(
                meter_coordinator,
                coordinator,
                entry,
                GaroSwitchEntityDescription(
                    key=key,
                    translation_key=key,
                    name=name,
                    icon=icon,
                    on_func=on_func,
                    off_func=off_func,
                    get_state=get_state,
                ),
                meter,
            ))

        if meter_coordinator.has_lb_config and (
            meter_coordinator.has_central100_meter
            or meter_coordinator.has_central101_meter
        ):
            primary_meter = (
                meter_coordinator.central100_meter
                if meter_coordinator.has_central100_meter
                else meter_coordinator.central101_meter
            )
            add_load_balancing_switch(
                primary_meter,
                "load_balancing_enabled",
                "Load Balancing",
                "mdi:scale-balance",
                lambda: meter_coordinator.async_set_lb_enabled(True),
                lambda: meter_coordinator.async_set_lb_enabled(False),
                lambda: meter_coordinator.lb_config.enabled,
            )


    async_add_entities(entities)


class GaroSwitchEntity(GaroEntity, SwitchEntity):
    """Representation of a Garo switch."""
    entity_description: GaroSwitchEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSwitchEntityDescription, always_available: bool = False):
        """Initialize the Switch."""
        self.entity_description = description
        self._always_available = always_available
        super().__init__(coordinator, entry, description.key)


    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.entity_description.is_available() and super().available if self.entity_description.is_available else super().available

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


class GaroLoadBalancingSwitchEntity(GaroMeterSwitchEntity):
    """Load-balancing switch entity grouped under the master charger."""

    def __init__(
        self,
        coordinator: GaroMeterCoordinator,
        device_coordinator: GaroDeviceCoordinator,
        entry,
        description: GaroSwitchEntityDescription,
        meter: GaroMeter,
    ):
        super().__init__(coordinator, entry, description, meter)
        self._device_coordinator = device_coordinator
        self._attr_unique_id = (
            f"{device_coordinator.device_id}-load_balancing-{description.key}"
        )
        self._attr_device_info = device_coordinator.device_info

    async def async_turn_on(self, **kwargs):
        """Turn on the switch and keep the API readback as the source of truth."""
        await self.entity_description.on_func()
        self._async_update_attrs()
        self.async_write_ha_state()
        self._device_coordinator.async_update_listeners()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch and keep the API readback as the source of truth."""
        await self.entity_description.off_func()
        self._async_update_attrs()
        self.async_write_ha_state()
        self._device_coordinator.async_update_listeners()
