from abc import abstractmethod

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .garo import GaroCharger, GaroMeter

class GaroEntity(CoordinatorEntity[GaroDeviceCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GaroDeviceCoordinator, config_entry, key: str, charger: GaroCharger | None = None) -> None:
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = key
        if charger is not None:
            self._attr_unique_id = f"charger_{charger.serial_number}-{key}"
            self._attr_device_info = coordinator.get_charger_device_info(charger)
        else:
            self._attr_unique_id = f"{coordinator.device_id}-{key}"
            self._attr_device_info = self.coordinator.device_info
        self._async_update_attrs()

    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        self.async_write_ha_state()

    @abstractmethod
    def _async_update_attrs(self) -> None:
        """Update the attributes of the entity."""

class GaroMeterEntity(CoordinatorEntity[GaroMeterCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GaroMeterCoordinator, config_entry, key: str, meter: GaroMeter) -> None:
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = key
        self._meter = meter
        self._attr_unique_id = f"meter_{meter.serial_number}-{key}"
        self._attr_device_info = coordinator.get_device_info(meter)
        self._async_update_attrs()

    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        self.async_write_ha_state()

    @abstractmethod
    def _async_update_attrs(self) -> None:
        """Update the attributes of the entity."""

