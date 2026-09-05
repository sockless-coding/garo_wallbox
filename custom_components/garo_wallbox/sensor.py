from datetime import time
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import config_validation as cv, entity_platform

from .garo import const, GaroCharger, GaroMeter
from .const import (SERVICE_SET_MODE, SERVICE_SET_CURRENT_LIMIT, SERVICE_SET_SCHEDULE, SERVICE_REMOVE_SCHEDULE, SERVICE_ADD_SCHEDULE)
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .base import GaroEntity, GaroMeterEntity
from . import GaroConfigEntry
from .sensor_descriptions import (
    GaroSensorEntityDescription,
    GaroChargerSensorEntityDescription,
    GaroMeterSensorEntityDescription,
    MAIN_SENSOR_DESCRIPTIONS,
    TWIN_SENSOR_DESCRIPTIONS,
    CHARGER_SENSOR_DESCRIPTIONS,
    SCHEDULE_SENSOR_DESCRIPTION,
    build_legacy_sensor_description,
    build_meter_sensor_descriptions,
)

_LOGGER = logging.getLogger(__name__)


def _register_services(platform) -> None:
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


async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        GaroSensorEntity(coordinator, entry, description) for description in MAIN_SENSOR_DESCRIPTIONS
    ]
    if coordinator.config.has_twin:
        entities.extend(
            GaroSensorEntity(coordinator, entry, description) for description in TWIN_SENSOR_DESCRIPTIONS
        )
    entities.append(
        GaroLegacySensorEntity(
            coordinator,
            entry,
            build_legacy_sensor_description(coordinator.main_charger_name),
        )
    )

    def add_charger_entities(charger: GaroCharger):
        entities.extend(
            GaroChargerSensorEntity(coordinator, entry, description, charger)
            for description in CHARGER_SENSOR_DESCRIPTIONS
        )
    entities.append(GaroScheduleSensorEntity(coordinator, entry))

    if coordinator.config.has_slaves:
        for slave in coordinator.slaves:
            add_charger_entities(slave)

    if entry.runtime_data.meter_coordinator:
        meter_coordinator = entry.runtime_data.meter_coordinator

        def add_meter_entities(meter: GaroMeter, is_3_phase: bool = True):
            entities.extend(
                GaroMeterSensorEntity(meter_coordinator, entry, description, meter)
                for description in build_meter_sensor_descriptions(meter_coordinator, is_3_phase)
            )

        if meter_coordinator.has_external_meter:
            add_meter_entities(meter_coordinator.external_meter, meter_coordinator.external_meter.type not in [103, 104])
        if meter_coordinator.has_central100_meter:
            add_meter_entities(meter_coordinator.central100_meter, meter_coordinator.central100_meter.type not in [103, 104])
        if meter_coordinator.has_central101_meter:
            add_meter_entities(meter_coordinator.central101_meter)

    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    if platform is not None:
        _register_services(platform)


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
        self.entity_description = SCHEDULE_SENSOR_DESCRIPTION
        super().__init__(coordinator, entry, self.entity_description.key)

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._entries = self.coordinator.schema
        self._attr_native_value = len(self._entries)
        _LOGGER.debug(f"Updated schedule entries: {len(self._entries)}")

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
