from typing import Callable, Any
from dataclasses import dataclass
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_ICON, 
    CONF_NAME)
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import UnitOfTemperature
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, EntityCategory
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription
)
from homeassistant.helpers import config_validation as cv, entity_platform, service

from . import DOMAIN as GARO_DOMAIN

from .garo import GaroStatus, const
from .const import (ATTR_MODES, SERVICE_SET_MODE, SERVICE_SET_CURRENT_LIMIT, DOMAIN, COORDINATOR)
from .coordinator import GaroDeviceCoordinator
from .base import GaroEntity

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class GaroSensorEntityDescription(SensorEntityDescription):
    """Describes Panasonic sensor entity."""
    get_state: Callable[[GaroStatus], Any]

MODE_DESCRIPTIONS = GaroSensorEntityDescription(
    key="sensor",
    translation_key="sensor",
    name="Mode",
    options=[opt.value for opt in const.Mode],
    device_class=SensorDeviceClass.ENUM,
    state_class=None,
    get_state=lambda status: status.mode.value,
)
STATUS_DESCRIPTION = GaroSensorEntityDescription(
    key="status",
    translation_key="status",
    name="Status",
    options=[opt.value for opt in const.Connector],
    device_class=SensorDeviceClass.ENUM,
    state_class=None,
    get_state=lambda status: status.connector.value,
)
CURRENT_CHARGING_CURRENT_DESCRIPTION = GaroSensorEntityDescription(
    key="current_charging_current",
    translation_key="current_charging_current",
    name="Charging Current",
    icon="mdi:flash",
    device_class=SensorDeviceClass.CURRENT,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="A",
    get_state=lambda status: status.current_charging_current,
)
CURRENT_CHARGING_POWER_DESCRIPTION = GaroSensorEntityDescription(
    key="current_charging_power",
    translation_key="current_charging_power",
    name="Charging Power",
    icon="mdi:flash",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="W",
    get_state=lambda status: status.current_charging_power,
)
PHASES_DESCRIPTION = GaroSensorEntityDescription(
    key="nr_of_phases",
    translation_key="nr_of_phases",
    name="Number of Phases",
    options=["1", "3"],
    device_class=SensorDeviceClass.ENUM,
    state_class=None,
    get_state=lambda status: str(status.number_of_phases),
)
CURRENT_LIMIT_DESCRIPTION = GaroSensorEntityDescription(
    key="current_limit",
    translation_key="current_limit",
    name="Current Limit",
    icon="mdi:gauge",
    device_class=SensorDeviceClass.CURRENT,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="A",
    get_state=lambda status: status.current_limit,
)
PILOT_LEVEL_DESCRIPTION = GaroSensorEntityDescription(
    key="pilot_level",
    translation_key="pilot_level",
    name="Pilot Level",
    icon="mdi:gauge",
    device_class=SensorDeviceClass.CURRENT,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="A",
    get_state=lambda status: status.pilot_level,
)
SESSION_ENERGY_DESCRIPTION = GaroSensorEntityDescription(
    key="acc_session_energy",
    translation_key="acc_session_energy",
    name="Session Energy",
    icon="mdi:flash-outline",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="kWh",
    get_state=lambda status: status.accumulated_session_energy,
)
TOTAL_ENERGY_DESCRIPTION = GaroSensorEntityDescription(
    key="latest_reading",
    translation_key="latest_reading",
    name="Total Energy",
    icon="mdi:flash",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="Wh",
    get_state=lambda status: status.latest_reading,
)
TOTAL_ENERGY_KWH_DESCRIPTION = GaroSensorEntityDescription(
    key="latest_reading_k",
    translation_key="latest_reading_k",
    name="Total Energy kWh",
    icon="mdi:flash",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
    native_unit_of_measurement="kWh",
    get_state=lambda status: status.latest_reading / 1000 if status.latest_reading else None,
)
TEMPERATURE_DESCRIPTION = GaroSensorEntityDescription(
    key="current_temperature",
    translation_key="current_temperature",
    name="Temperature",
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="°C",
    get_state=lambda status: status.current_temperature,
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    pass


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coorinator = hass.data[DOMAIN][COORDINATOR]
    async_add_entities([
        PanasonicSensorEntity(coorinator, entry,MODE_DESCRIPTIONS),
        PanasonicSensorEntity(coorinator, entry,STATUS_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,CURRENT_CHARGING_CURRENT_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,CURRENT_CHARGING_POWER_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,PHASES_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,CURRENT_LIMIT_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,PILOT_LEVEL_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,SESSION_ENERGY_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,TOTAL_ENERGY_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,TOTAL_ENERGY_KWH_DESCRIPTION),
        PanasonicSensorEntity(coorinator, entry,TEMPERATURE_DESCRIPTION),
        ])

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



class PanasonicSensorEntity(GaroEntity, SensorEntity):
    
    entity_description: GaroSensorEntityDescription

    def __init__(self, coordinator: GaroDeviceCoordinator, entry, description: GaroSensorEntityDescription):
        self.entity_description = description
        super().__init__(coordinator, entry, description.key)

  
    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.get_state(self.coordinator.status)


