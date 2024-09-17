from typing import Callable, Any
from dataclasses import dataclass
from datetime import time
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


from .garo import GaroStatus, const, GaroCharger, GaroMeter
from .const import (SERVICE_SET_MODE, SERVICE_SET_CURRENT_LIMIT, SERVICE_SET_SCHEDULE, SERVICE_REMOVE_SCHEDULE, SERVICE_ADD_SCHEDULE)
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .base import GaroEntity, GaroMeterEntity
from . import GaroConfigEntry

AVAILABLE_PHASE_COUNTS = ["1","2","3"]

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class GaroSensorEntityDescription(SensorEntityDescription):
    """Describes Garo sensor entity."""
    get_state: Callable[[GaroStatus], Any]

@dataclass(frozen=True, kw_only=True)
class GaroChargerSensorEntityDescription(SensorEntityDescription):
    """Describes Garo sensor entity."""
    get_state: Callable[[GaroCharger], Any]

@dataclass(frozen=True, kw_only=True)
class GaroMeterSensorEntityDescription(SensorEntityDescription):
    """Describes Garo sensor entity."""
    get_state: Callable[[GaroMeter], Any]


async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    entities:list[SensorEntity] = [
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
                options=AVAILABLE_PHASE_COUNTS,
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
                options=AVAILABLE_PHASE_COUNTS,
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
                options=AVAILABLE_PHASE_COUNTS,
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
                name="Right Energy",
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
    
    def add_charger_entities(charger: GaroCharger):
        entities.extend(GaroChargerSensorEntity(coordinator, entry, description, charger) for description in [    
            GaroChargerSensorEntityDescription(
                key="status",
                translation_key="status",
                name="Status",
                options=[opt.value for opt in const.Connector],
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda charger: charger.connector.value,
            ),
            GaroChargerSensorEntityDescription(
                key="current_charging_current",
                translation_key="current_charging_current",
                name="Charging Current",
                icon="mdi:flash",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda charger: charger.current_charging_current,
            ),
            GaroChargerSensorEntityDescription(
                key="current_charging_power",
                translation_key="current_charging_power",
                name="Charging Power",
                icon="mdi:flash",
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfPower.WATT,
                get_state=lambda charger: charger.current_charging_power,
            ),
            GaroChargerSensorEntityDescription(
                key="nr_of_phases",
                translation_key="nr_of_phases",
                name="Number of Phases",
                options=AVAILABLE_PHASE_COUNTS,
                device_class=SensorDeviceClass.ENUM,
                state_class=None,
                get_state=lambda charger: str(charger.number_of_phases),
            ),
            GaroChargerSensorEntityDescription(
                key="pilot_level",
                translation_key="pilot_level",
                name="Pilot Level",
                icon="mdi:gauge",
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                get_state=lambda charger: charger.pilot_level,
            ),
            GaroChargerSensorEntityDescription(
                key="acc_session_energy",
                translation_key="acc_session_energy",
                name="Session Energy",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
                get_state=lambda charger: charger.accumulated_session_energy,
            ),
            GaroChargerSensorEntityDescription(
                key="session_time",
                translation_key="session_time",
                name="Session Time",
                icon="mdi:flash-outline",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MILLISECONDS,
                get_state=lambda charger: charger.accumulated_session_millis,
            ),
            GaroChargerSensorEntityDescription(
                key="acc_energy",
                translation_key="acc_energy",
                name="Total Energy",
                icon="mdi:flash",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                get_state=lambda charger: charger.accumulated_energy / 1000 if charger.accumulated_energy else None,
            )
        ])
    entities.append(GaroScheduleSensorEntity(coordinator, entry))

    if coordinator.config.has_slaves:
        for slave in coordinator.slaves:
            add_charger_entities(slave)

    if entry.runtime_data.meter_coordinator:
        meter_coordinator = entry.runtime_data.meter_coordinator
        def add_meter_sentities(meter: GaroMeter, is_3_phase: bool = True):
            entities.extend(GaroMeterSensorEntity(meter_coordinator, entry, description, meter) for description in [    
                GaroMeterSensorEntityDescription(
                    key="meter_l1_current",
                    translation_key="meter_l1_current",
                    name="Current phase L1",
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    get_state=lambda meter: meter.l1_current,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_l2_current",
                    translation_key="meter_l2_current",
                    name="Current phase L2",
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    get_state=lambda meter: meter.l2_current,
                    entity_registry_enabled_default=is_3_phase
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_l3_current",
                    translation_key="meter_l3_current",
                    name="Current phase L3",
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    get_state=lambda meter: meter.l3_current,
                    entity_registry_enabled_default=is_3_phase,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_l1_power",
                    translation_key="meter_l1_power",
                    name="Power consumption phase L1",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfPower.KILO_WATT,
                    get_state=lambda meter: meter.l1_power,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_l2_power",
                    translation_key="meter_l2_power",
                    name="Power consumption phase L2",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfPower.KILO_WATT,
                    get_state=lambda meter: meter.l2_power,
                    entity_registry_enabled_default=is_3_phase,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_l3_power",
                    translation_key="meter_l3_power",
                    name="Power consumption phase L3",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfPower.KILO_WATT,
                    get_state=lambda meter: meter.l3_power,
                    entity_registry_enabled_default=is_3_phase,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_power_consumption",
                    translation_key="meter_power_consumption",
                    name="Power consumption",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfPower.KILO_WATT,
                    get_state=lambda meter: meter.apparent_power,
                ),
                GaroMeterSensorEntityDescription(
                    key="meter_accumulated_energy",
                    translation_key="meter_accumulated_energy",
                    name="Energy consumption (total)",
                    device_class=SensorDeviceClass.ENERGY,
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                    get_state=lambda meter: meter.accumulated_energy,
                )])
        
        if meter_coordinator.has_external_meter:
            add_meter_sentities(meter_coordinator.external_meter, meter_coordinator.external_meter.type not in [103,104])
        if meter_coordinator.has_central100_meter:
            add_meter_sentities(meter_coordinator.central100_meter, meter_coordinator.central100_meter.type not in [103,104])
        if meter_coordinator.has_central101_meter:
            add_meter_sentities(meter_coordinator.central101_meter)

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
        platform.async_register_entity_service(
            SERVICE_ADD_SCHEDULE,
            {
                vol.Required('start'): cv.time,
                vol.Required('stop'): cv.time,
                vol.Required('day_of_the_week'): cv.enum(const.SchemaDayOfWeek),
                vol.Optional('charge_limit'): cv.positive_int,
            },
            "async_add_schedule",
        )
        platform.async_register_entity_service(
            SERVICE_SET_SCHEDULE,
            {
                vol.Required('id'): cv.positive_int,
                vol.Required('start'): cv.time,
                vol.Required('stop'): cv.time,
                vol.Required('day_of_the_week'): cv.enum(const.SchemaDayOfWeek),
                vol.Optional('charge_limit'): cv.positive_int,
            },
            "async_set_schedule",
        )
        platform.async_register_entity_service(
            SERVICE_REMOVE_SCHEDULE,
            {
                vol.Required('id'): cv.positive_int,
            },
            "async_remove_schedule",
        )
        



class GaroSensorEntity(GaroEntity, SensorEntity):
    
    entity_description: GaroSensorEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)

  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.get_state(self.coordinator.status)

class GaroChargerSensorEntity(GaroEntity, SensorEntity):
    
    entity_description: GaroChargerSensorEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroChargerSensorEntityDescription, charger: GaroCharger):
        self.entity_description = description
        self._charger = charger
        super().__init__(coordinator, entry, description.key, charger)

  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.get_state(self._charger)

class GaroMeterSensorEntity(GaroMeterEntity, SensorEntity):
    
    entity_description: GaroMeterSensorEntityDescription

    def __init__(self, coordinator: GaroMeterCoordinator, entry, description: GaroMeterSensorEntityDescription, meter: GaroMeter):
        self.entity_description = description
        self._meter = meter
        super().__init__(coordinator, entry, description.key, meter)

  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.get_state(self._meter)


class GaroLegacySensorEntity(GaroSensorEntity):

    async def async_set_mode(self, mode):
        await self.coordinator.api_client.async_set_mode(mode)

    async def async_set_current_limit(self, limit):
        await self.coordinator.api_client.async_set_current_limit(limit)

class GaroScheduleSensorEntity(GaroEntity, SensorEntity):
    

    def __init__(self, coordinator: GaroDeviceCoordinator, entry):
        self.entity_description = SensorEntityDescription(
            key="schedule",
            translation_key="schedule",
            icon="mdi:calendar-clock",
            name="Schedule",
            state_class=None
        )
        super().__init__(coordinator, entry, self.entity_description.key)
  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._entries = self.coordinator.schema
        self._attr_native_value = len(self._entries)
        
    @property
    def entries(self):
        return [{
            'id': entry.id,
            'start': entry.start,
            'stop': entry.stop,
            'day_of_the_week': entry.day_of_the_week.name,
            'charge_limit': entry.charge_limit
        } for entry in self._entries]

    @property
    def state_attributes(self):
        """Return the data of the entity."""
        output = {
            "entries": self.entries,
        }
        return output
    
    async def async_add_schedule(self, start:str|time, stop:str|time, day_of_the_week: const.SchemaDayOfWeek | int, charge_limit: int = 0):
        if isinstance(day_of_the_week, const.SchemaDayOfWeek):
            day_of_the_week = day_of_the_week.value
        await self.coordinator.async_set_schema(0, start, stop, day_of_the_week, charge_limit)
        self._async_update_attrs()
        self.async_write_ha_state()
    
    async def async_set_schedule(self, id:int, start: str|time, stop:str|time, day_of_the_week: const.SchemaDayOfWeek | int, charge_limit: int = 0):
        if isinstance(day_of_the_week, const.SchemaDayOfWeek):
            day_of_the_week = day_of_the_week.value
        await self.coordinator.async_set_schema(id, start, stop, day_of_the_week, charge_limit)
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_remove_schedule(self, id:int):
        await self.coordinator.async_remove_schema(id)
        self._async_update_attrs()
        self.async_write_ha_state()
