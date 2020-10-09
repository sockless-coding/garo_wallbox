import logging

import requests
import time
from enum import Enum
from datetime import timedelta
import asyncio

from homeassistant.util import Throttle
from .const import GARO_PRODUCT_MAP, DOMAIN

current_milli_time = lambda: int(round(time.time() * 1000))

MODE_ON, MODE_OFF, MODE_SCHEMA = ('ALWAYS_ON', 'ALWAYS_OFF', 'SCHEMA')
STATUS_CHANGING, STATUS_NOT_CONNECTED, STATUS_CONNECTED, STATUS_SEARCH_COMM = ('CHANGING','NOT_CONNECTED','CONNECTED','SEARCH_COMM')

HEADER_JSON = {'content-type': 'application/json; charset=utf-8'}

_LOGGER = logging.getLogger(__name__)

class Mode(Enum):
    On = MODE_ON
    Off = MODE_OFF
    Schema = MODE_SCHEMA


class Status(Enum):
    CHANGING = 'CHANGING'
    NOT_CONNECTED = 'NOT_CONNECTED'
    CONNECTED = 'CONNECTED'
    SEARCH_COMM = 'SEARCH_COMM'
    RCD_FAULT = 'RCD_FAULT'
    CHARGING = 'CHARGING'
    CHARGING_PAUSED = 'CHARGING_PAUSED'
    CHARGING_FINISHED = 'CHARGING_FINISHED'
    CHARGING_CANCELLED = 'CHARGING_CANCELLED'
    OVERHEAT = 'OVERHEAT'
    CRITICAL_TEMPERATURE = 'CRITICAL_TEMPERATURE'
    INITIALIZATION = 'INITIALIZATION'
    CABLE_FAULT = 'CABLE_FAULT'
    LOCK_FAULT = 'LOCK_FAULT'
    CONTACTOR_FAULT = 'CONTACTOR_FAULT'
    VENT_FAULT = 'VENT_FAULT'
    DC_ERROR = 'DC_ERROR'
    UNKNOWN = 'UNKNOWN'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

class GaroDevice:

    def __init__(self, host, name, session):
        self.host = host
        self.name = name
        self._status = None
        self._session = session
    
    async def init(self):
        await self.async_get_info()
        self.id = 'garo_{}'.format(self.info.serial)
        if self.name is None:
            self.name = f'{self.info.model} ({self.host})'
        await self.async_update()

    @property
    def status(self):
        return self._status

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "identifiers": { (DOMAIN, self.id) },
            "manufacturer": "Garo",
            "model": self.info.model,
            "name": self.name,
        }

    def _request(self, parameter_list):
        pass
    
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        await self._do_update()

    async def _do_update(self):
        response = await self._session.request(method='GET', url=self.__get_url('status', True))
        response_json = await response.json()
        self._status = GaroStatus(response_json)

    async def async_get_info(self):
        response = await self._session.request(method='GET', url=self.__get_url('config', True))
        response_json = await response.json()
        self.info = GaroDeviceInfo(response_json)

    async def set_mode(self, mode: Mode):
        response = await self._session.post(self.__get_url('mode'), data=mode.value, headers = HEADER_JSON)
        await response.text()
        await self._do_update()

    async def set_current_limit(self, limit):
        response = await self._session.request(method='GET', url=self.__get_url('config', True))
        response_json = await response.json()
        response_json['reducedCurrentIntervals'] = [{
            'chargeLimit': str(limit),
            'schemaId': 1,
            'start': '00:00:00',
            'stop':'24:00:00',
            'weekday': 8
        }]
        #_LOGGER.warning(f'Set limit: {response_json}')
        response = await self._session.post(self.__get_url('config'), json=response_json, headers = HEADER_JSON)
        await response.text()
        await self._do_update()


    def __get_url(self, action, add_tick = False):
        return 'http://{}:2222/rest/chargebox/{}{}'.format(self.host, action, '' if add_tick == False else '?_={}'.format(current_milli_time()))

class GaroStatus:

    def __init__(self,response):
        self.ocpp_state = response['ocppState']
        self.free_charging = response['freeCharging']
        self.ocpp_connection_state = response['ocppConnectionState']
        self.status = Status(response['connector'])
        self.mode = Mode(response['mode'])
        self.current_limit = response['currentLimit']
        self.factory_current_limit = response['factoryCurrentLimit']
        self.switch_current_limit = response['switchCurrentLimit']
        self.power_mode = response['powerMode']
        self.current_charging_current = max(0,response['currentChargingCurrent'] / 1000)
        self.current_charging_power = max(0,response['currentChargingPower'])
        self.acc_session_energy = response['accSessionEnergy']
        self.latest_reading = response['latestReading']
        self.current_temperature = response['currentTemperature']
        self.pilot_level = response['pilotLevel']
        self.session_start_value = response['sessionStartValue']
        self.nr_of_phases = response['nrOfPhases']

class GaroDeviceInfo:

    def __init__(self,response):
        self.serial = response['serialNumber']
        self.productId = response['productId']
        self.model = GARO_PRODUCT_MAP[int(self.productId)]
        self.max_current = response['maxChargeCurrent']