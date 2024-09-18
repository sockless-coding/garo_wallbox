"""Garo Wallbox integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict
from dataclasses import dataclass

from aiohttp import ClientConnectionError
from async_timeout import timeout

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_NAME,
    CONF_HOST,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .garo import ApiClient, GaroConfig
from .coordinator import GaroDeviceCoordinator, GaroMeterCoordinator
from .const import (
    DOMAIN,
    TIMEOUT,
    COMPONENT_TYPES,
    COORDINATOR
)

PLATFORMS = [SENSOR_DOMAIN]
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

type GaroConfigEntry = ConfigEntry[GaroRuntimeData]

@dataclass
class GaroRuntimeData:
    """Runtime data definition."""

    coordinator: GaroDeviceCoordinator
    meter_coordinator: GaroMeterCoordinator | None

async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the Garo Wallbox component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry):

    session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    api_client = ApiClient(session, host)
    try:
        with timeout(TIMEOUT):
            configuration = await api_client.async_get_configuration()
        coordinator = GaroDeviceCoordinator(hass, entry, api_client, configuration)
        await coordinator.async_config_entry_first_refresh()
        try:
            with timeout(5):
                await coordinator.async_fetch_schema()
        except Exception:
            _LOGGER.exception("Failed to fetch schema")
            pass
        meter_coordinator: GaroMeterCoordinator | None = None
        if configuration.has_load_balancer:
            meter_coordinator = GaroMeterCoordinator(hass, entry, api_client, configuration)
            await meter_coordinator.async_config_entry_first_refresh()
        entry.runtime_data = GaroRuntimeData(
            coordinator=coordinator,
            meter_coordinator=meter_coordinator 
        )
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, coordinator.device_id)},
            manufacturer="Garo",
            model=coordinator.config.product.name,
            name=coordinator.main_charger_name,
            serial_number=str(coordinator.config.serial_number),
            sw_version=coordinator.config.package_version
        )
        if configuration.has_slaves:
            for slave in coordinator.slaves:
                slave_charger = coordinator.get_charger_device_info(slave)
                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers=slave_charger.get("identifiers"),
                    manufacturer="Garo")
                
        if configuration.has_load_balancer and meter_coordinator is not None:
            if meter_coordinator.has_external_meter:
                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers=meter_coordinator.get_device_info(meter_coordinator.external_meter).get("identifiers"),
                    manufacturer="Garo")
            if meter_coordinator.has_central100_meter:
                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers=meter_coordinator.get_device_info(meter_coordinator.central100_meter).get("identifiers"),
                    manufacturer="Garo")
            if meter_coordinator.has_central101_meter:
                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers=meter_coordinator.get_device_info(meter_coordinator.central101_meter).get("identifiers"),
                    manufacturer="Garo")

        await hass.config_entries.async_forward_entry_setups(entry, COMPONENT_TYPES)
        return True
    except asyncio.TimeoutError:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady
    except ClientConnectionError:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        return False


async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, COMPONENT_TYPES)

async def garo_setup(hass: HomeAssistant, entry: ConfigEntry):
    """Create a Garo instance only once."""
    session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    api_client = ApiClient(session, host)
    try:
        with timeout(TIMEOUT):
            configuration = await api_client.async_get_configuration()
        return GaroDeviceCoordinator(hass, entry, api_client, configuration)

    except asyncio.TimeoutError:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady
    except ClientConnectionError:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        return None

