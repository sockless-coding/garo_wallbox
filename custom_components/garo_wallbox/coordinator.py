import logging

from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

from .garo import ApiClient, GaroConfig, GaroStatus, GaroCharger
from .garo.const import CableLockMode, PRODUCT_MAP, GaroProductInfo
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
        self._name = self._config.master_charger.reference or entry.data[CONF_NAME]
        self._slaves = self._config.slaves

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
        return self._name

    @property
    def slaves(self) -> list[GaroCharger]:        
        return [slave for slave in self._slaves if slave.serial_number != self._config.serial_number and slave.serial_number != self._config.twin_serial]


    @property
    def device_info(self)->DeviceInfo:
        return DeviceInfo(            
            identifiers={(const.DOMAIN, str(self._id) )},
            manufacturer="Garo",
            model=self._config.product.name,
            name=self.main_charger_name,
            serial_number=str(self._config.serial_number),
            sw_version=self._config.package_version,
            hw_version=f"{self._config.firmware_version}.{self._config.firmware_revision}"
        )
    
    def get_charger_device_info(self, charger: GaroCharger)->DeviceInfo:
        product = self.get_product_info(charger)
        return DeviceInfo(            
            identifiers={(const.DOMAIN, f"garo_charger_{charger.serial_number}" )},
            manufacturer="Garo",
            model=product.name,
            name=charger.reference if charger.reference else f"Charger {charger.serial_number}",
            serial_number=str(charger.serial_number),
            sw_version=self._config.package_version,
            hw_version=f"{charger.firmware_version}.{charger.firmware_revision}"
        )
    
    def get_product_info(self, charger: GaroCharger)->GaroProductInfo:
        product_id = self._config.product_id if charger.serial_number == self._config.master_charger.serial_number else charger.product_id
        return PRODUCT_MAP[product_id] if product_id in PRODUCT_MAP else GaroProductInfo('Unknown')


       
    async def async_enable_charge_limit(self, enable: bool):
        await self._api_client.async_enable_charge_limit(enable)
        self._config = await self._api_client.async_get_configuration()

    async def async_set_cable_lock_mode(self, serial_number: int, mode: CableLockMode| str):
        if isinstance(mode, str):
            mode = CableLockMode[mode]
        await self._api_client.async_set_cable_lock_mode(serial_number, mode)

    async def _fetch_device_data(self)->int:
        try:
            self._status = await self._api_client.async_get_status(self._status)
            has_changed = self._status.has_changed
            if (self._config.has_slaves):
                await self._api_client.async_get_slaves(self._slaves)
                for slave in self._slaves:
                    if slave.has_changed:
                        has_changed = True
                        break
            if has_changed:
                self._update_id += 1
        except BaseException as e:
            _LOGGER.error("Error fetching device data from API: %s", e, exc_info=e)
            raise UpdateFailed(f"Invalid response from API: {e}") from e
        return self._update_id