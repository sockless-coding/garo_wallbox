"""Garo Wallbox integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict

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
from .coordinator import GaroDeviceCoordinator
from .const import (
    DOMAIN,
    TIMEOUT,
    COMPONENT_TYPES,
    COORDINATOR
)

PLATFORMS = [SENSOR_DOMAIN]
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the Garo Wallbox component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):

    session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    api_client = ApiClient(session, host)
    try:
        with timeout(TIMEOUT):
            configuration = await api_client.async_get_configuration()
        coordinator = GaroDeviceCoordinator(hass, entry, api_client, configuration)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][COORDINATOR] = coordinator
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

