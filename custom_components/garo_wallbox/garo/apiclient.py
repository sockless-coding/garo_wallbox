import aiohttp
import logging
import time

from .garostatus import GaroStatus
from .garoconfig import GaroConfig
from .garocharger import GaroCharger
from . import const

_LOGGER = logging.getLogger(__name__)

current_milli_time = lambda: int(round(time.time() * 1000))

class ApiClient:

    def __init__(self, client: aiohttp.ClientSession, host: str):
        self._client = client
        self._host = host
        self._pre_v1_3 = False

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
        return GaroConfig(data)
    
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
        
    
    async def async_set_mode(self, mode: const.Mode | str):
        if isinstance(mode, str):
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
            response_json['cableLockMode'] = mode.value
            response = await self._async_post(self._get_url('cablelock'), data=response_json)
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
        
