import logging

from homeassistant.const import CONF_ICON, CONF_NAME, TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

from . import DOMAIN as GARO_DOMAIN

from .garo import GaroDevice, Mode, Status

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    pass


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    device = hass.data[GARO_DOMAIN].get(entry.entry_id)
    async_add_entities([
        GaroSensor(device, 'Status', 'status'), 
        GaroSensor(device, 'Mode', 'mode'), 
        GaroSensor(device, "Charging Current", 'current_charging_current', 'A'),
        GaroSensor(device, "Charging Power", 'current_charging_power', 'W'),
        GaroSensor(device, "Phases", 'nr_of_phases'),
        GaroSensor(device, "Current Limit", 'current_limit', 'A'),
        GaroSensor(device, "Pilot Level", 'pilot_level', 'A'),
        GaroSensor(device, "Temperature", 'current_temperature', TEMP_CELSIUS)
        ])

class GaroSensor(Entity):
    def __init__(self, device: GaroDevice, name, sensor, unit = None):
        """Initialize the sensor."""
        self._device = device
        self._name = f"{device.id} {name}"
        self._sensor = sensor
        self._unit = unit

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device.id}-{self._sensor}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the sensor."""
        icon = None
        if self._sensor == "current_temperature":
            icon = "mdi:thermometer"
        elif self._sensor == "current_charging_current":
            icon = "mdi:flash"
        elif self._sensor == "current_charging_power":
            icon = "mdi:flash"
        elif self._sensor == "current_limit":
            icon = "mdi:flash"
        elif self._sensor == "pilot_level":
            icon = "mdi:flash"
        
        return icon

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensor == 'mode':
            return self.mode_as_str()
        if self._sensor == 'status':
            return self.status_as_str()

        return self._device.status.__dict__[self._sensor]

    @property
    def unit_of_measurement(self):
        return self._unit

    async def async_update(self):
        await self._device.async_update()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._device.device_info

    def mode_as_str(self):
        switcher = {
            Mode.ON: 'On',
            Mode.OFF: 'Off',
            Mode.SCHEMA: 'Schema'
        }
        return switcher.get(self._device.status.mode, "Unknown")

    def status_as_str(self):
        switcher = {
            Status.CABLE_FAULT: "Cable fault",
            Status.CHANGING: "Changing...",
            Status.CHARGING: "Charging",
            Status.CHARGING_CANCELLED: "Charging cancelled",
            Status.CHARGING_FINISHED: "Charging finished",
            Status.CHARGING_PAUSED: "Charging paused",
            Status.CONNECTED: "Vehicle connected",
            Status.CONTACTOR_FAULT: "Contactor fault",
            Status.CRITICAL_TEMPERATURE: "Overtemperature, charging cancelled",
            Status.DC_ERROR: "DC error",
            Status.INITIALIZATION: "Charger starting...",
            Status.LOCK_FAULT: "Lock fault",
            Status.NOT_CONNECTED: "Vehicle not connected",
            Status.OVERHEAT: "Overtemperature, charging temporarily restricted to 6A",
            Status.RCD_FAULT: "RCD fault",
            Status.SEARCH_COMM: "Vehicle connected",
            Status.VENT_FAULT: "Ventilation required"
        }
        return switcher.get(self._device.status.status, "Unknown")