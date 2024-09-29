from abc import abstractmethod

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .garo import GaroCharger, GaroMeter
from homeassistant.const import CONF_TYPE
from .const import EVENT_NAME, EVENT_TYPE_DATA_UPDATED


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

    async def async_added_to_hass(self) -> None:
        """Add event listener to update data when sensor added to hass."""
        await super().async_added_to_hass()
        # _LOGGER.debug(f"Sensor '{self.name}' added to Hass")
        # Listen for event and update sensor
        self.hass.bus.async_listen(EVENT_NAME, self.async_handle_event)

    @callback
    async def async_handle_event(self, event):
        """Handle an event and update state."""
        if event.data.get(CONF_TYPE) == EVENT_TYPE_DATA_UPDATED:
            # _LOGGER.debug(f"Event captured: '{EVENT_NAME}' is of type '{EVENT_TYPE_DATA_UPDATED}'")
            self._async_update_attrs()
            self.async_write_ha_state()
        else:
            # _LOGGER.debug(f"Event ignored: '{EVENT_NAME}' is of type '{EVENT_TYPE_DATA_UPDATED}'")
            pass

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

