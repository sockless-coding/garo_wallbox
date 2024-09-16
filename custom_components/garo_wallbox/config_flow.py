"""Config flow for the Garo Wallbox platform."""
import asyncio
import logging
from typing import Any, Dict, Optional

from aiohttp import ClientConnectionError
from async_timeout import timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession


from .const import TIMEOUT, DOMAIN, CONF_DEVICE_FETCH_INTERVAL, CONF_METER_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL, DEFAULT_METER_FETCH_INTERVAL
from .garo import ApiClient
from . import GaroConfigEntry

_LOGGER = logging.getLogger(__name__)

class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GaroOptionsFlowHandler(config_entry)

    async def _create_entry(self, host, name, device_fetch_interval = None, meter_fetch_interval = None):
        """Register new entry."""
        # Check if ip already is registered
        for entry in self._async_current_entries():
            if entry.data[CONF_HOST] == host:
                return self.async_abort(reason="already_configured")

        return self.async_create_entry(
            title=host, 
            data={
                CONF_HOST: host, 
                CONF_NAME: name,
            },
            options={                
                CONF_DEVICE_FETCH_INTERVAL: device_fetch_interval or DEFAULT_DEVICE_FETCH_INTERVAL,
                CONF_METER_FETCH_INTERVAL: meter_fetch_interval or DEFAULT_METER_FETCH_INTERVAL
            })

    async def _create_device(self, host, name, device_fetch_interval = None, meter_fetch_interval= None):
        """Create device."""
        session = async_get_clientsession(self.hass)
        api_client = ApiClient(session, host)
        try:
            with timeout(TIMEOUT):
                await api_client.async_get_configuration()
            return await self._create_entry(host, name,device_fetch_interval, meter_fetch_interval)
        except asyncio.TimeoutError:
            _LOGGER.debug("Connection to %s timed out", host)
            return self.async_abort(reason="device_timeout")
        except ClientConnectionError:
            _LOGGER.debug("ClientConnectionError to %s", host)
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error creating device %s", host, exc_info=e)
        return self.async_abort(reason="device_fail")
        

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_NAME): str,
                    vol.Optional(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=DEFAULT_DEVICE_FETCH_INTERVAL,
                    ): int,
                    vol.Optional(
                        CONF_METER_FETCH_INTERVAL,
                        default=DEFAULT_METER_FETCH_INTERVAL,
                    ): int,
                })
            )
        return await self._create_device(
            user_input[CONF_HOST], 
            user_input[CONF_NAME],
            user_input[CONF_DEVICE_FETCH_INTERVAL],
            user_input[CONF_METER_FETCH_INTERVAL])

    async def async_step_import(self, user_input):
        """Import a config entry."""
        host = user_input.get(CONF_HOST)
        if not host:
            return await self.async_step_user()
        return await self._create_device(host, user_input[CONF_NAME])

    async def async_step_discovery(self, user_input):
        """Initialize step from discovery."""
        _LOGGER.info("Discovered device: %s", user_input)
        return await self._create_entry(user_input[CONF_HOST], None)

class GaroOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Garo options."""

    def __init__(self, config_entry: GaroConfigEntry):
        """Initialize Garo options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: Optional[Dict[str, Any]] = None
    ):
        """Manage Garo options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST),
                    ): str,
                    vol.Optional(
                        CONF_NAME,
                        default=self.config_entry.data.get(CONF_NAME),
                    ): str,
                    vol.Optional(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_METER_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_METER_FETCH_INTERVAL, DEFAULT_METER_FETCH_INTERVAL
                        ),
                    ): int,
                }
            ),
        )