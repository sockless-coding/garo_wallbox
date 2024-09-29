from typing import Callable, Awaitable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .garo import GaroStatus, const, GaroCharger
from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from .const import DOMAIN,COORDINATOR
from . import GaroConfigEntry

@dataclass(frozen=True, kw_only=True)
class GaroSelectEntityDescription(SelectEntityDescription):
    """Description of a select entity."""
    set_option: Callable[[str], Awaitable]
    get_current_option: Callable[[GaroStatus], str]
    is_available: Callable[[], bool] | None = None

@dataclass(frozen=True, kw_only=True)
class GaroChargerSelectEntityDescription(SelectEntityDescription):
    """Description of a select entity."""
    set_option: Callable[[str], Awaitable]
    get_current_option: Callable[[GaroCharger], str]
    is_available: Callable[[], bool] | None = None

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    api_client = coordinator.api_client
    config = coordinator.config
    descriptions = [
        GaroSelectEntityDescription(
            key="sensor",
            translation_key="sensor",
            name=coordinator.main_charger_name,
            icon="mdi:ev-station",
            options=[opt.value for opt in const.Mode],
            set_option=lambda option: api_client.async_set_mode(option),
            get_current_option=lambda status: status.mode.value
        ),
    ]
    if config.has_outlet:
        descriptions.append(
            GaroSelectEntityDescription(
                key="left_outlet" if config.has_twin else "outlet",
                translation_key="left_outlet" if config.has_twin else "outlet",
                name="Left Outlet" if config.has_twin else "Outlet",
                icon="mdi:ev-plug-type2",
                options=[opt.name for opt in const.CableLockMode],
                set_option=lambda option: coordinator.async_set_cable_lock_mode(config.serial_number, option),
                get_current_option=lambda status: status.main_charger.cable_lock_mode.name))
        if config.has_twin:
            descriptions.append(
                GaroSelectEntityDescription(
                    key="right_outlet",
                    translation_key="right_outlet",
                    name="Right Outlet",
                    icon="mdi:ev-plug-type2",
                    options=[opt.name for opt in const.CableLockMode],
                    set_option=lambda option: coordinator.async_set_cable_lock_mode(config.twin_serial, option),
                    get_current_option=lambda status: status.twin_charger.cable_lock_mode.name))
    entries:list[SelectEntity] = [GaroSelectEntity(coordinator, entry, description) for description in descriptions]
    if config.has_slaves:
        for slave in config.slaves:
            product = coordinator.get_product_info(slave)
            if not product.has_outlet:
                continue
            entries.append(GaroChargerSelectEntity(
                coordinator, 
                entry, 
                GaroChargerSelectEntityDescription(
                    key="outlet",
                    translation_key="outlet",
                    name= "Outlet",
                    icon="mdi:ev-plug-type2",
                    options=[opt.name for opt in const.CableLockMode],
                    set_option=lambda option: coordinator.async_set_cable_lock_mode(slave.serial_number, option),
                    get_current_option=lambda charger: charger.cable_lock_mode.name),
                    slave))
    async_add_entities(entries)
       

class GaroSelectEntity(GaroEntity, SelectEntity):

    entity_description: GaroSelectEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSelectEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""        
        return self.entity_description.is_available() if self.entity_description.is_available else super().available
    
    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_option(option)
        await self.coordinator._fetch_device_data()
        self._attr_current_option = option
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self.current_option = self.entity_description.get_current_option(self.coordinator.status)

class GaroChargerSelectEntity(GaroEntity, SelectEntity):

    entity_description: GaroChargerSelectEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroChargerSelectEntityDescription, charger: GaroCharger):
        self.entity_description = description
        self._charger = charger
        super().__init__(coordinator, entry, description.key, charger)

    @property
    def available(self) -> bool:
        """Return if entity is available."""        
        return self.entity_description.is_available() if self.entity_description.is_available else super().available
    
    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_option(option)
        self._attr_current_option = option
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self.current_option = self.entity_description.get_current_option(self._charger)