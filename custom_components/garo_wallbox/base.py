from abc import abstractmethod

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import GaroDeviceCoordinator

class GaroEntity(CoordinatorEntity[GaroDeviceCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GaroDeviceCoordinator, config_entry, key: str) -> None:
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = key
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

