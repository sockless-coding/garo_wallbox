import aiohttp
import logging
import time

_LOGGER = logging.getLogger(__name__)

current_milli_time = lambda: int(round(time.time() * 1000))

class ApiClient:

    def __init__(self, client: aiohttp.ClientSession, host: str):
        self._client = client
        self._host = host
        self._pre_v1_3 = False

    async def async_get_status(self):
        response = await self._client.request(method='GET', url=self._get_url('status', True))
        if response.status != 200 and not self._pre_v1_3:
            self._pre_v1_3 = True
            _LOGGER.info('Switching to pre v1.3.1 endpoint')
            response = await self._client.request(method='GET', url=self._get_url('status', True))
        if response.status != 200 and self._pre_v1_3:
            _LOGGER.error('Could not connect to chargebox')
            raise ConnectionError


    def _get_url(self, action, add_tick = False):
        tick = '' if add_tick == False else '?_={}'.format(current_milli_time())
        if self._pre_v1_3:
            return f'http://{self._host}:2222/rest/chargebox/{action}{tick}'
        return f'http://{self._host}:8080/servlet/rest/chargebox/{action}{tick}'
        
