import logging

import requests
import time
from enum import Enum
from datetime import timedelta
import asyncio

from homeassistant.util import Throttle
from .const import GARO_PRODUCT_MAP, DOMAIN, VOLTAGE, LOCAL_METER_PATH, GROUP_METER_PATH, GROUP101_METER_PATH, \
    CURRENT_DIVIDER

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
    DISABLED = 'DISABLED'
    OVERHEAT = 'OVERHEAT'
    CRITICAL_TEMPERATURE = 'CRITICAL_TEMPERATURE'
    INITIALIZATION = 'INITIALIZATION'
    CABLE_FAULT = 'CABLE_FAULT'
    LOCK_FAULT = 'LOCK_FAULT'
    CONTACTOR_FAULT = 'CONTACTOR_FAULT'
    VENT_FAULT = 'VENT_FAULT'
    DC_ERROR = 'DC_ERROR'
    UNKNOWN = 'UNKNOWN'
    UNAVAILABLE = 'UNAVAILABLE'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=15)

class GaroDevice:

    def __init__(self, host, name, session):
        self.host = host
        self.name = name
        self._status = None
        self._session = session
        self._pre_v1_3 = False
        self.meter= None

    async def init(self):
        await self.async_get_info()
        self.id = 'garo_{}'.format(self.info.serial)
        if self.name is None:
            self.name = f'{self.info.model} ({self.host})'
        if self.info.meter_path:
            # load balancing unit with energy meter was found
            self.meter = MeterDevice(self)
            await self.meter.init()
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
        if response.status != 200 and not self._pre_v1_3:
            self._pre_v1_3 = True
            _LOGGER.info('Switching to pre v1.3.1 endpoint')
            response = await self._session.request(method='GET', url=self.__get_url('status', True))


        response_json = await response.json()
        self._status = GaroStatus(response_json, self._status)

    async def async_get_info(self):
        response = await self._session.request(method='GET', url=self.__get_url('config', True))
        _LOGGER.info(f'Response {response}')
        if response.status != 200 and not self._pre_v1_3:
            self._pre_v1_3 = True
            _LOGGER.info('Switching to pre v1.3.1 endpoint')
            response = await self._session.request(method='GET', url=self.__get_url('config', True))

        response_json = await response.json()
        self.info = GaroDeviceInfo(response_json)

    async def set_mode(self, mode: Mode):
        if self._pre_v1_3:
            response = await self._session.post(self.__get_url('mode'), data=mode.value, headers = HEADER_JSON)
        else:
            response = await self._session.post(self.__get_url(f'mode/{mode.value}'), headers = HEADER_JSON)
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
        if self._pre_v1_3:
            return 'http://{}:2222/rest/chargebox/{}{}'.format(self.host, action, '' if add_tick == False else '?_={}'.format(current_milli_time()))
        return 'http://{}:8080/servlet/rest/chargebox/{}{}'.format(self.host, action, '' if add_tick == False else '?_={}'.format(current_milli_time()))

    async def get_json_response(self, action, add_tick):
        url = self.__get_url(action, add_tick)
        response = await self._session.request(method='GET', url=url)
        json_response = await response.json()
        return json_response


class GaroStatus:

    def __init__(self,response, prev_status):
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
        if self.current_charging_power > 32000:
            self.current_charging_power = 0
        self.acc_session_energy = response['accSessionEnergy']
        last_reading = response['latestReading']
        if prev_status is not None and last_reading - prev_status.latest_reading > 500000:
            last_reading = prev_status.latest_reading

        self.latest_reading = last_reading
        self.latest_reading_k = max(0,last_reading /1000)
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
        if response.get('localLoadBalanced'):
            self.meter_path = LOCAL_METER_PATH
        elif response.get('groupLoadBalanced'):
            self.meter_path = GROUP_METER_PATH
        elif response.get('groupLoadBalanced101'):
            self.meter_path = GROUP101_METER_PATH
        else:
            self.meter_path = None


class MeterDevice:
    def __init__(self, device):
        self.main_device = device
        self.name = device.name + " meter"
        self.meter_action = f'meterinfo/{device.info.meter_path}'
        self.status = None
        self.id = None

    async def init(self):
        await self.async_update()
        self.id = 'garo_{}'.format(self.status.serial)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "identifiers": {(DOMAIN, self.id)},
            "manufacturer": "Garo",
            "model": self.status.type,
            "name": self.name,
            "via_device": (DOMAIN, self.main_device.id)
        }

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        json = await self.main_device.get_json_response(self.meter_action, True)
        self.status = MeterStatus(json, self.status)


class MeterStatus:

    def __init__(self, response, prev_status):
        last_serial = response['meterSerial']
        if prev_status is None or last_serial is prev_status.serial:
            self.serial = last_serial
            self.type = response['type']
            # TODO, use current divider based on firmware version
            self.phase1_current = response['phase1Current'] / CURRENT_DIVIDER
            self.phase2_current = response['phase2Current'] / CURRENT_DIVIDER
            self.phase3_current = response['phase3Current'] / CURRENT_DIVIDER
            current = self.phase1_current + self.phase2_current + self.phase3_current
            self.power = int(round(current * VOLTAGE, -1))
            self.acc_energy_k = round(response['accEnergy'] / 1000, 1)
        _LOGGER.debug(self.__dict__)
