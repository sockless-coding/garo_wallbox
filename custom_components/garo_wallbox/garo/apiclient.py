import aiohttp
import logging
import time

from .garostatus import GaroStatus
from .garoconfig import GaroConfig
from .garocharger import GaroCharger

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
    
    async def async_get_slaves(self) -> list[GaroCharger]:
        response = await self._async_get('slaves/false')
        data = await response.json()
        return [GaroCharger(d) for d in data]

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

    def _get_url(self, action, add_tick = False):
        tick = '' if add_tick == False else '?_={}'.format(current_milli_time())
        if self._pre_v1_3:
            return f'http://{self._host}:2222/rest/chargebox/{action}{tick}'
        return f'http://{self._host}:8080/servlet/rest/chargebox/{action}{tick}'
        
