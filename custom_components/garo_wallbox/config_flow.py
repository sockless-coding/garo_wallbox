"""Config flow for the Garo Wallbox platform."""
import asyncio
import logging

from aiohttp import ClientConnectionError
from async_timeout import timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession


from .const import TIMEOUT
from .garo import ApiClient

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register("garo_wallbox")
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def _create_entry(self, host, name):
        """Register new entry."""
        # Check if ip already is registered
        for entry in self._async_current_entries():
            if entry.data[CONF_HOST] == host:
                return self.async_abort(reason="already_configured")

        return self.async_create_entry(title=host, data={CONF_HOST: host, CONF_NAME: name})

    async def _create_device(self, host, name):
        """Create device."""
        session = async_get_clientsession(self.hass)
        api_client = ApiClient(session, host)
        try:
            with timeout(TIMEOUT):
                await api_client.async_get_configuration()
            return await self._create_entry(host, name)
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
                    vol.Optional(CONF_NAME): str
                    })
            )
        return await self._create_device(user_input[CONF_HOST], user_input[CONF_NAME])

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
