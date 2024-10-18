import logging

from datetime import timedelta, datetime, time
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.storage import Store

from .garo import ApiClient, GaroConfig, GaroStatus, GaroCharger, GaroMeter, GaroSchema
from .garo.const import CableLockMode, PRODUCT_MAP, GaroProductInfo, Mode as GaroMode
from . import const

_LOGGER = logging.getLogger(__name__)

METER_CALCULATE_POWER = 'meter_calculate_power'
METER_VOLTAGE = 'meter_voltage'

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
        self._status: GaroStatus | None = None
        self._name = self._config.master_charger.reference or entry.data[CONF_NAME]
        self._slaves = self._config.slaves
        self._schema: list[GaroSchema] = []


        self._update_id = 0

    @property
    def api_client(self) -> ApiClient:
        return self._api_client
    
    @property
    def device_id(self) -> str:
        return self._id
    
    @property
    def status(self) -> GaroStatus:
        if not self._status:
            raise ValueError("Status is not initialized")
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
    def schema(self) -> list[GaroSchema]:
        return self._schema

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
        self.async_update_listeners()

    async def async_set_cable_lock_mode(self, serial_number: int, mode: CableLockMode| str):
        if isinstance(mode, str):
            mode = CableLockMode[mode]
        await self._api_client.async_set_cable_lock_mode(serial_number, mode)
        await self.async_request_refresh()

    async def async_fetch_schema(self):
        try:
            self._schema = await self._api_client.async_get_schema()
            self.async_update_listeners()
            _LOGGER.debug("Fetched {} schemas".format(len(self._schema)))
        except Exception as e:
            _LOGGER.error("Failed to fetch schema: {}".format(e), exc_info=e)
        

    async def async_set_schema(self, id:int, start:str|time, stop:str|time, day_of_the_week: int, charge_limit: int):
        if isinstance(start, str):
            start = datetime.strptime(start, "%H:%M:%S" if start.count(':') == 2 else "%H:%M").time()
        if isinstance(stop, str):
            stop = datetime.strptime(stop, "%H:%M:%S" if stop.count(':') == 2 else "%H:%M").time()
        await self._api_client.async_set_schema(
            id, 
            start, 
            stop,  
            day_of_the_week, 
            charge_limit)
        await self.async_fetch_schema()

    async def async_remove_schema(self, id:int):
        await self._api_client.async_remove_schema(id)
        await self.async_fetch_schema()
        
    async def async_set_mode(self, mode: GaroMode | str):
        await self._api_client.async_set_mode(mode)
        await self.async_request_refresh()

    async def async_set_current_limit(self, limit: int):
        await self._api_client.async_set_current_limit(limit)
        await self.async_request_refresh()


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
    
class GaroMeterCoordinator(DataUpdateCoordinator[int]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api_client: ApiClient, config: GaroConfig) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Garo Meter Coordinator",
            update_interval=timedelta(seconds=entry.options.get(const.CONF_METER_FETCH_INTERVAL, const.DEFAULT_METER_FETCH_INTERVAL)),
            update_method=self._fetch_device_data,
        )
        self._hass = hass
        self._entry = entry
        self._config = config
        self._api_client = api_client
        self._external_meter: GaroMeter | None = None
        self._central100_meter: GaroMeter | None = None
        self._central101_meter: GaroMeter | None = None
        self._store = Store(hass, version=1, key="garo_meter")
        self._stored_data: dict|None = None
        
        self._update_id = 0

    @property
    def has_external_meter(self) -> bool:
        return self._external_meter is not None
    @property
    def external_meter(self)->GaroMeter:
        if not self._external_meter:
            raise ValueError("External meter not initialized")
        return self._external_meter
    
    @property
    def has_central100_meter(self) -> bool:
        return self._central100_meter is not None
    @property
    def central100_meter(self)->GaroMeter:
        if not self._central100_meter:
            raise ValueError("Central 100 meter not initialized")
        return self._central100_meter
    
    @property
    def has_central101_meter(self) -> bool:
        return self._central101_meter is not None
    @property
    def central101_meter(self)->GaroMeter:
        if not self._central101_meter:
            raise ValueError("Central 101 meter not initialized")
        return self._central101_meter
    
    @property
    def calculate_power(self)->bool:
        if self._stored_data is None:
            raise ValueError("Stored data is not initialized")        
        return self._stored_data[METER_CALCULATE_POWER] if METER_CALCULATE_POWER in self._stored_data else True
    
    @property
    def voltage(self)->int:
        if self._stored_data is None:
            raise ValueError("Stored data is not initialized")
        return int(self._stored_data[METER_VOLTAGE]) if METER_VOLTAGE in self._stored_data else 230
    
    def get_device_info(self, meter: GaroMeter)->DeviceInfo:
        
        return DeviceInfo(            
            identifiers={(const.DOMAIN, f"garo_meter_{meter.serial_number}" )},
            manufacturer="Garo",
            name=f"Energy meter ({meter.serial_number})",
            model=f"Type {meter.type}",
            serial_number=str(meter.serial_number),
        )
    
    async def async_set_calculate_power(self, calculate_power:bool):
        """Set calculate power."""
        if self._stored_data is None:
            raise ValueError("Stored data is not initialized")
        _LOGGER.debug(f"Setting calculate power to {calculate_power}")
        self._stored_data[METER_CALCULATE_POWER] = calculate_power
        await self._store.async_save(self._stored_data)
        self.async_update_listeners()

    async def async_set_voltage(self, voltage:int):
        """Set voltage."""
        if self._stored_data is None:
            raise ValueError("Stored data is not initialized")
        _LOGGER.debug(f"Setting voltage to {voltage}")
        self._stored_data[METER_VOLTAGE] = voltage
        await self._store.async_save(self._stored_data)
        self.async_update_listeners()


    async def _fetch_device_data(self)->int:
        try:
            has_changed = False
            if not self._stored_data:
                self._stored_data = await self._store.async_load() or {}
                _LOGGER.debug("Loaded stored data: %s", self._stored_data)
            if self._config.local_load_balanced:
                self._external_meter = await self._api_client.async_get_external_meter(self._external_meter)
                if self._external_meter.has_changed:
                    has_changed = True
            if self._config.group_load_balanced:
                self._central100_meter = await self._api_client.async_get_central100_meter(self._central100_meter)
                if self._central100_meter.has_changed:
                    has_changed = True
            if self._config.group_load_balanced101:
                self._central101_meter = await self._api_client.async_get_central101_meter(self._central101_meter)
                if self._central101_meter.has_changed:
                    has_changed = True
            
            if has_changed:
                self._update_id += 1
        except BaseException as e:
            _LOGGER.error("Error fetching meter data from API: %s", e, exc_info=e)
            raise UpdateFailed(f"Invalid response from API: {e}") from e
        return self._update_id