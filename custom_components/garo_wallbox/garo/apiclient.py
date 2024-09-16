import aiohttp
import logging
import time

from .garostatus import GaroStatus
from .garoconfig import GaroConfig
from .garocharger import GaroCharger
from .garometer import GaroMeter
from . import const

_LOGGER = logging.getLogger(__name__)

current_milli_time = lambda: int(round(time.time() * 1000))

class ApiClient:

    def __init__(self, client: aiohttp.ClientSession, host: str):
        self._client = client
        self._host = host
        self._pre_v1_3 = False
        self._configuration: GaroConfig | None = None
        self._has_meter_info = False
        self._current_divider = 1
        self._power_divider = 1


    async def async_get_status(self, status: GaroStatus | None = None):
        response = await self._async_get('status')
        data = await response.json()
        if not status:
            status = GaroStatus(data)
        else:
            status.load(data)
        return status
    
    async def async_get_configuration(self):
        response = await self._async_get('config')
        data = await response.json()
        self._configuration = GaroConfig(data)
        return self._configuration
    
    async def async_get_slaves(self, slaves: list[GaroCharger] | None = None) -> list[GaroCharger]:
        response = await self._async_get('slaves/false')
        data = await response.json()
        if not slaves:
            slaves = []
        for d in data:
            if 'serialNumber' not in d:
                continue
            serial_number = d['serialNumber']
            has_found = False
            for s in slaves:
                if s.serial_number == serial_number:
                    s.load(d)
                    has_found = True
                    break
            if not has_found:
                slaves.append(GaroCharger(d))
        return slaves
    
    async def async_get_external_meter(self, meter: GaroMeter | None = None) -> GaroMeter:        
        return await self._async_get_meter('meterinfo/EXTERNAL', meter)
    
    async def async_get_central100_meter(self, meter: GaroMeter | None = None) -> GaroMeter:
        return await self._async_get_meter('meterinfo/CENTRAL100', meter)
    
    async def async_get_central101_meter(self, meter: GaroMeter | None = None) -> GaroMeter:
        return await self._async_get_meter('meterinfo/CENTRAL101', meter)
    
    async def _async_get_meter(self, endpoint:str, meter: GaroMeter | None = None) -> GaroMeter:
        await self._async_load_meter_info()
        response = await self._async_get(endpoint)
        data = await response.json()
        if meter is None:
            meter = GaroMeter(data, self._current_divider, self._power_divider)
        else:
            meter.load(data)
        return meter
		
        
    
    async def async_set_mode(self, mode: const.Mode | str):
        if isinstance(mode, str):
            if mode.upper() == 'ON':
                mode = const.Mode.ON
            elif mode.upper() == 'OFF':
                mode = const.Mode.OFF
            else:
                mode = const.Mode(mode)
        if self._pre_v1_3:
            response = await self._async_post(self._get_url('mode'), data=mode.value)
        else:
            response = await self._async_post(self._get_url(f'mode/{mode.value}'))
        await response.text()

    async def async_set_current_limit(self, limit: int):
        response = await self._async_get('config', True)
        response_json = await response.json()
        response_json['reducedCurrentIntervals'] = [{
            'chargeLimit': str(limit),
            'schemaId': 1,
            'start': '00:00:00',
            'stop':'24:00:00',
            'weekday': 8
        }]
        response = await self._async_post(self._get_url('config'), data=response_json)
        await response.text()

    async def async_enable_charge_limit(self, enable: bool):
        response = await self._async_get('config', True)
        response_json = await response.json()
        response_json['reducedIntervalsEnabled'] = enable
        response = await self._async_post(self._get_url('currentlimit'), data=response_json)
        await response.text()
        
    async def async_set_cable_lock_mode(self, serial_number: int, mode: const.CableLockMode):
        response = await self._async_get('slaves/false', True)
        response_json = await response.json()
        for slave in response_json:
            if slave['serialNumber'] != serial_number:
                continue
            slave['cableLockMode'] = mode.value
            response = await self._async_post(self._get_url('cablelock'), data=slave)
            await response.text()
            return
        raise ValueError('Slave with serial number {} not found'.format(serial_number))
        

    async def _async_get(self, action: str, add_tick = False):
        response = await self._client.request(method='GET', url=self._get_url(action, add_tick))
        if response.status != 200 and not self._pre_v1_3:
            self._pre_v1_3 = True
            _LOGGER.info('Switching to pre v1.3.1 endpoint')
            response = await self._client.request(method='GET', url=self._get_url(action, add_tick))
        if response.status != 200 and self._pre_v1_3:
            _LOGGER.error('Could not connect to chargebox')
            raise ConnectionError
        return response
    
    async def _async_post(self, url: str, data=None):
        response = await self._client.request(
            method='POST', 
            url=url, 
            json=data,
            headers={'content-type': 'application/json; charset=utf-8'})
        return response

    def _get_url(self, action, add_tick = False):
        tick = '' if add_tick == False else '?_={}'.format(current_milli_time())
        if self._pre_v1_3:
            return f'http://{self._host}:2222/rest/chargebox/{action}{tick}'
        return f'http://{self._host}:8080/servlet/rest/chargebox/{action}{tick}'
    
    async def _async_load_meter_info(self):
        if self._has_meter_info:
            return
        config = self._configuration or await self.async_get_configuration()
        self._current_divider = 1
        self._power_divider = 1
		
        if config.firmware_version == 2 and config.firmware_revision <= 12:
            self._current_divider = 1000
            self._power_divider = 1000
        elif (config.firmware_version == 2 and config.firmware_revision >= 13) or config.firmware_version > 7 or (config.firmware_version == 7 and config.firmware_revision >= 7):
            self._current_divider = 10
        self._has_meter_info = True
        
