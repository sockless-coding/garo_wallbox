"""Config flow for the Garo Wallbox platform."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError
from async_timeout import timeout
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEVICE_FETCH_INTERVAL,
    CONF_METER_FETCH_INTERVAL,
    DEFAULT_DEVICE_FETCH_INTERVAL,
    DEFAULT_METER_FETCH_INTERVAL,
    DOMAIN,
    TIMEOUT,
)
from .garo import ApiClient, GaroConfig

_LOGGER = logging.getLogger(__name__)

MIN_FETCH_INTERVAL = 5
MAX_FETCH_INTERVAL = 3600

_INTERVAL = vol.All(vol.Coerce(int), vol.Range(min=MIN_FETCH_INTERVAL, max=MAX_FETCH_INTERVAL))


class CannotConnect(Exception):
    """Raised when the wallbox cannot be reached."""


async def _async_get_charger_config(hass, host: str) -> GaroConfig:
    """Connect to the wallbox and return its configuration.

    Raises CannotConnect if the device is unreachable or misbehaving.
    """
    api_client = ApiClient(async_get_clientsession(hass), host)
    try:
        async with timeout(TIMEOUT):
            return await api_client.async_get_configuration()
    except (asyncio.TimeoutError, ClientError, ConnectionError) as err:
        raise CannotConnect from err


class FlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Garo Wallbox config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return GaroOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                config = await _async_get_charger_config(self.hass, host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error connecting to %s", host)
                errors["base"] = "unknown"
            else:
                if config.serial_number:
                    await self.async_set_unique_id(str(config.serial_number))
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                else:
                    self._async_abort_entries_match({CONF_HOST: host})

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or host,
                    data={
                        CONF_HOST: host,
                        CONF_NAME: user_input.get(CONF_NAME) or host,
                    },
                    options={
                        CONF_DEVICE_FETCH_INTERVAL: DEFAULT_DEVICE_FETCH_INTERVAL,
                        CONF_METER_FETCH_INTERVAL: DEFAULT_METER_FETCH_INTERVAL,
                    },
                )

        suggested = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=suggested.get(CONF_HOST, vol.UNDEFINED)
                    ): str,
                    vol.Optional(
                        CONF_NAME, default=suggested.get(CONF_NAME, vol.UNDEFINED)
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing entry (change host / name)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                config = await _async_get_charger_config(self.hass, host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error connecting to %s", host)
                errors["base"] = "unknown"
            else:
                updates: dict[str, Any] = {
                    "data_updates": {
                        CONF_HOST: host,
                        CONF_NAME: user_input.get(CONF_NAME) or host,
                    }
                }
                if config.serial_number:
                    await self.async_set_unique_id(str(config.serial_number))
                    # Legacy entries were created without a unique_id; adopt the
                    # serial number then, and only guard against a genuine swap.
                    if entry.unique_id is not None:
                        self._abort_if_unique_id_mismatch(reason="wrong_device")
                    updates["unique_id"] = self.unique_id

                return self.async_update_reload_and_abort(entry, **updates)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or entry.data).get(CONF_HOST),
                    ): str,
                    vol.Optional(
                        CONF_NAME,
                        default=(user_input or entry.data).get(CONF_NAME),
                    ): str,
                }
            ),
            errors=errors,
        )


class GaroOptionsFlowHandler(OptionsFlow):
    """Handle Garo Wallbox options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the polling intervals."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=options.get(
                            CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL
                        ),
                    ): _INTERVAL,
                    vol.Required(
                        CONF_METER_FETCH_INTERVAL,
                        default=options.get(
                            CONF_METER_FETCH_INTERVAL, DEFAULT_METER_FETCH_INTERVAL
                        ),
                    ): _INTERVAL,
                }
            ),
        )
