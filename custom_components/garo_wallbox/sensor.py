from typing import Callable, Any
from dataclasses import dataclass
import logging

import voluptuous as vol


from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription
)
from homeassistant.helpers import config_validation as cv, entity_platform


from .garo import GaroStatus, const
from .const import (SERVICE_SET_MODE, SERVICE_SET_CURRENT_LIMIT, DOMAIN, COORDINATOR)
from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity
from . import GaroConfigEntry

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class GaroSensorEntityDescription(SensorEntityDescription):
    """Describes Garo sensor entity."""
    get_state: Callable[[GaroStatus], Any]



async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    entities = [
        GaroSensorEntity(coordinator, entry, description) for description in [            
            GaroSensorEntityDescription(
                key="status",
                translation_key="status",
                name="Status",
                options=[opt.value for opt in const.Connector],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: status.connector.value,
            ),
            GaroSensorEntityDescription(
                key="current_charging_current",
                translation_key="current_charging_current",
                name="Charging Current",
                icon="mdi:flash",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.current_charging_current,
            ),
            GaroSensorEntityDescription(
                key="current_charging_power",
                translation_key="current_charging_power",
                name="Charging Power",
                icon="mdi:flash",
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfPower.WATT,
                get_state=lambda status: status.current_charging_power,
            ),
            GaroSensorEntityDescription(
                key="nr_of_phases",
                translation_key="nr_of_phases",
                name="Number of Phases",
                options=["1", "3"],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: str(status.number_of_phases),
            ),
            GaroSensorEntityDescription(
                key="current_limit",
                translation_key="current_limit",
                name="Current Limit",
                icon="mdi:gauge",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.current_limit,
            ),
            GaroSensorEntityDescription(
                key="pilot_level",
                translation_key="pilot_level",
                name="Pilot Level",
                icon="mdi:gauge",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.pilot_level,
            ),
            GaroSensorEntityDescription(
                key="acc_session_energy",
                translation_key="acc_session_energy",
                name="Session Energy",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
                get_state=lambda status: status.accumulated_session_energy,
            ),
            GaroSensorEntityDescription(
                key="session_time",
                translation_key="session_time",
                name="Session Time",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MILLISECONDS,
                get_state=lambda status: status.accumulated_session_millis,
            ),
            GaroSensorEntityDescription(
                key="latest_reading",
                translation_key="latest_reading",
                name="Total Energy",
                icon="mdi:flash",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
                get_state=lambda status: status.latest_reading,
            ),
            GaroSensorEntityDescription(
                key="latest_reading_k",
                translation_key="latest_reading_k",
                name="Total Energy kWh",
                icon="mdi:flash",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                get_state=lambda status: status.latest_reading / 1000 if status.latest_reading else None,
            ),
            GaroSensorEntityDescription(
                key="current_temperature",
                translation_key="current_temperature",
                name="Temperature",
                icon="mdi:thermometer",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                get_state=lambda status: status.current_temperature,
            )
        ]]
    if (coordinator.config.has_twin):
        entities.extend(GaroSensorEntity(coordinator, entry, description) for description in [    
            GaroSensorEntityDescription(
                key="left_status",
                translation_key="left_status",
                name="Left Status",
                options=[opt.value for opt in const.Connector],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: status.main_charger.connector.value,
            ),
            GaroSensorEntityDescription(
                key="left_current_charging_current",
                translation_key="left_current_charging_current",
                name="Left Charging Current",
                icon="mdi:flash",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.main_charger.current_charging_current,
            ),
            GaroSensorEntityDescription(
                key="left_current_charging_power",
                translation_key="left_current_charging_power",
                name="Left Charging Power",
                icon="mdi:flash",
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfPower.WATT,
                get_state=lambda status: status.main_charger.current_charging_power,
            ),
            GaroSensorEntityDescription(
                key="left_nr_of_phases",
                translation_key="left_nr_of_phases",
                name="Left Number of Phases",
                options=["1", "3"],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: str(status.main_charger.number_of_phases),
            ),
            GaroSensorEntityDescription(
                key="left_pilot_level",
                translation_key="left_pilot_level",
                name="Left Pilot Level",
                icon="mdi:gauge",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.main_charger.pilot_level,
            ),
            GaroSensorEntityDescription(
                key="left_acc_session_energy",
                translation_key="left_acc_session_energy",
                name="Left Session Energy",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
                get_state=lambda status: status.main_charger.accumulated_session_energy,
            ),
            GaroSensorEntityDescription(
                key="left_session_time",
                translation_key="left_session_time",
                name="Left Session Time",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MILLISECONDS,
                get_state=lambda status: status.main_charger.accumulated_session_millis,
            ),
            GaroSensorEntityDescription(
                key="left_acc_energy",
                translation_key="left_acc_energy",
                name="Left Energy",
                icon="mdi:flash",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                get_state=lambda status: status.main_charger.accumulated_energy / 1000 if status.main_charger.accumulated_energy else None,
            ),
            GaroSensorEntityDescription(
                key="right_status",
                translation_key="right_status",
                name="Right Status",
                options=[opt.value for opt in const.Connector],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: status.twin_charger.connector.value,
            ),
            GaroSensorEntityDescription(
                key="right_current_charging_current",
                translation_key="right_current_charging_current",
                name="Right Charging Current",
                icon="mdi:flash",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.twin_charger.current_charging_current,
            ),
            GaroSensorEntityDescription(
                key="right_current_charging_power",
                translation_key="right_current_charging_power",
                name="Right Charging Power",
                icon="mdi:flash",
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfPower.WATT,
                get_state=lambda status: status.twin_charger.current_charging_power,
            ),
            GaroSensorEntityDescription(
                key="right_nr_of_phases",
                translation_key="right_nr_of_phases",
                name="Right Number of Phases",
                options=["1", "3"],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: str(status.twin_charger.number_of_phases),
            ),
            GaroSensorEntityDescription(
                key="right_pilot_level",
                translation_key="right_pilot_level",
                name="Right Pilot Level",
                icon="mdi:gauge",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda status: status.twin_charger.pilot_level,
            ),
            GaroSensorEntityDescription(
                key="right_acc_session_energy",
                translation_key="right_acc_session_energy",
                name="Right Session Energy",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
                get_state=lambda status: status.twin_charger.accumulated_session_energy,
            ),
            GaroSensorEntityDescription(
                key="right_session_time",
                translation_key="right_session_time",
                name="Right Session Time",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MILLISECONDS,
                get_state=lambda status: status.twin_charger.accumulated_session_millis,
            ),
            GaroSensorEntityDescription(
                key="right_acc_energy",
                translation_key="right_acc_energy",
                name="Left Energy",
                icon="mdi:flash",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                get_state=lambda status: status.twin_charger.accumulated_energy / 1000 if status.twin_charger.accumulated_energy else None,
            ),
        ])
    entities.append(
        GaroLegacySensorEntity(
            coordinator, 
            entry, 
            GaroSensorEntityDescription(
                key="sensor",
                translation_key="sensor",
                name=coordinator.main_charger_name,
                icon="mdi:car-electric",
                options=[opt.value for opt in const.Mode],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda status: status.mode.value,
            )
        ))
    
   
    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    if platform is not None:
        platform.async_register_entity_service(
            SERVICE_SET_MODE,
            {
                vol.Required('mode'): cv.string,
            },
            "async_set_mode",
        )
        platform.async_register_entity_service(
            SERVICE_SET_CURRENT_LIMIT,
            {
                vol.Required('limit'): cv.positive_int,
            },
            "async_set_current_limit",
        )



class GaroSensorEntity(GaroEntity, SensorEntity):
    
    entity_description: GaroSensorEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)

  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.get_state(self.coordinator.status)


class GaroLegacySensorEntity(GaroSensorEntity):

    async def async_set_mode(self, mode):
        await self.coordinator.api_client.async_set_mode(mode)

    async def async_set_current_limit(self, limit):
        await self.coordinator.api_client.async_set_current_limit(limit)
