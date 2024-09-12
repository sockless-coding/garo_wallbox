import logging

from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

from .garo import ApiClient, GaroConfig, GaroStatus
from .garo.const import CableLockMode
from . import const

_LOGGER = logging.getLogger(__name__)

class GaroDeviceCoordinator(DataUpdateCoordinator[int]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api_client: ApiClient, config: GaroConfig) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Garo Device Coordinator",
            update_interval=timedelta(seconds=entry.options.get(const.CONF_DEVICE_FETCH_INTERVAL, const.DEFAULT_DEVICE_FETCH_INTERVAL)),
            update_method=self._fetch_device_data,
        )
        self._hass = hass
        self._entry = entry
        self._config = config
        self._api_client = api_client
        self._id = f"garo_{config.serial_number}"
        self._status: GaroStatus = None

        self._update_id = 0

    @property
    def api_client(self) -> ApiClient:
        return self._api_client
    
    @property
    def device_id(self) -> str:
        return self._id
    
    @property
    def status(self) -> GaroStatus:
        return self._status
    
    @property
    def config(self) -> GaroConfig:
        return self._config
       
    @property
    def main_charger_name(self) -> str:
        return self._config.devices[0].reference

    @property
    def device_info(self)->DeviceInfo:
        return DeviceInfo(
            identifiers={(const.DOMAIN, str(self._id) )},
            manufacturer="Garo",
            model=self._config.product.name,
            name=self.main_charger_name,
            sw_version=self._config.package_version
        )
       
    async def async_enable_charge_limit(self, enable: bool):
        await self._api_client.async_enable_charge_limit(enable)
        self._config = await self._api_client.async_get_configuration()

    async def async_set_cable_lock_mode(self, serial_number: int, mode: CableLockMode| str):
        pass

    async def _fetch_device_data(self)->int:
        try:
            self._status = await self._api_client.async_get_status(self._status)
            if self._status.has_changed:
                self._update_id += 1
        except BaseException as e:
            _LOGGER.error("Error fetching device data from API: %s", e, exc_info=e)
            raise UpdateFailed(f"Invalid response from API: {e}") from e
        return self._update_id