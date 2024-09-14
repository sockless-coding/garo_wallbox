import logging

from . import const, utils

logger = logging.getLogger(__name__)

class GaroCharger:

    def __init__(self, json = None):
        
        self._is_valid = False
        self._reference	= ''
        self._serial_number = 0
        self._online = False
        self._load_balanced = False
        self._phase = 0
        self._product_id = 0
        self._charge_status = 0
        self._pilot_level = 0
        self._accumulated_energy = 0
        self._firmware_version = 0
        self._firmware_revision = 0
        self._connector = const.Connector.UNKNOWN
        self._accumulated_session_energy = 0
        self._accumulated_session_millis = 0
        self._current_charging_current = 0.0
        self._current_charging_power = 0
        self._number_of_phases = 1
        self._twin_serial = -1
        self._cable_lock_mode = const.CableLockMode.UNLOCKED
        self._min_current_limit = 6

        self._has_changed = False
        self.load(json)

    def load(self, json) -> bool:
        if json is None:
            return False
        self._is_valid = True
        

        self.reference = utils.read_value(json,'reference', self._reference)
        self.serial_number = utils.read_value(json,'serialNumber', self._serial_number)
        self.online = utils.read_value(json,'online', self._online)
        self.load_balanced = utils.read_value(json,'loadBalanced', self._load_balanced)
        self.phase = utils.read_value(json,'phase', self._phase)
        self.product_id = utils.read_value(json,'productId', self._product_id)
        self.charge_status = utils.read_value(json,'chargeStatus', self._charge_status)
        self.pilot_level = utils.read_value(json,'pilotLevel', self._pilot_level)
        self.accumulated_energy = utils.read_value(json,'accEnergy', self._accumulated_energy)
        self.firmware_version = utils.read_value(json,'firmwareVersion', self._firmware_version)
        self.firmware_revision = utils.read_value(json,'firmwareRevision', self._firmware_revision)
        self.connector = utils.read_enum(json,'connector', const.Connector, self._connector)
        self.accumulated_session_energy = utils.read_value(json,'accSessionEnergy', self._accumulated_session_energy)
        self.accumulated_session_millis = utils.read_value(json,'accSessionMillis', self._accumulated_session_millis)
        self.current_charging_current = utils.read_value(json,'currentChargingCurrent', self._current_charging_current)
        self.current_charging_power = utils.read_value(json,'currentChargingPower', self._current_charging_power)
        self.number_of_phases = utils.read_value(json,'nrOfPhases', self._number_of_phases)
        self.twin_serial = utils.read_value(json,'twinSerial', self._twin_serial)
        self.cable_lock_mode = utils.read_enum(json,'cableLockMode', const.CableLockMode, self._cable_lock_mode)
        self.min_current_limit = utils.read_value(json,'minCurrentLimit', self._min_current_limit)



        has_changed = self._has_changed
        self._has_changed = False
        return has_changed

    @property
    def is_valid(self):
        return self._is_valid
    
    @property
    def reference(self) -> str:
        return self._reference
    @reference.setter
    def reference(self, value):
        if self._reference == value:
            return
        self._reference = value
        self._has_changed = True

    @property
    def serial_number(self):
        return self._serial_number
    @serial_number.setter
    def serial_number(self, value):
        if self._serial_number == value:
            return
        self._serial_number = value
        self._has_changed = True

    @property
    def online(self) -> bool:
        return self._online
    @online.setter
    def online(self, value):
        if self._online == value:
            return
        self._online = value
        self._has_changed = True

    @property
    def load_balanced(self):
        return self._load_balanced
    @load_balanced.setter
    def load_balanced(self, value):
        if self._load_balanced == value:
            return
        self._load_balanced = value
        self._has_changed = True

    @property
    def phase(self):
        return self._phase
    @phase.setter
    def phase(self, value):
        if self._phase == value:
            return
        self._phase = value
        self._has_changed = True

    @property
    def product_id(self):
        return self._product_id
    @product_id.setter
    def product_id(self, value):
        if self._product_id == value:
            return
        self._product_id = value
        self._has_changed = True

    @property
    def charge_status(self):
        return self._charge_status
    @charge_status.setter
    def charge_status(self, value):
        if self._charge_status == value:
            return
        self._charge_status = value
        self._has_changed = True

    @property
    def pilot_level(self):
        return self._pilot_level
    @pilot_level.setter
    def pilot_level(self, value):
        if self._pilot_level == value:
            return
        self._pilot_level = value
        self._has_changed = True

    @property
    def accumulated_energy(self):
        return self._accumulated_energy
    @accumulated_energy.setter
    def accumulated_energy(self, value):
        if self._accumulated_energy == value:
            return
        self._accumulated_energy = value
        self._has_changed = True

    @property
    def firmware_version(self):
        return self._firmware_version
    @firmware_version.setter
    def firmware_version(self, value):
        if self._firmware_version == value:
            return
        self._firmware_version = value
        self._has_changed = True

    @property
    def firmware_revision(self):
        return self._firmware_revision
    @firmware_revision.setter
    def firmware_revision(self, value):
        if self._firmware_revision == value:
            return
        self._firmware_revision = value
        self._has_changed = True

    @property
    def connector(self):        
        return self._connector
    @connector.setter
    def connector(self, value):
        if self._connector == value:
            return
        self._connector = value
        self._has_changed = True

    @property
    def accumulated_session_energy(self):
        return self._accumulated_session_energy
    @accumulated_session_energy.setter
    def accumulated_session_energy(self, value):
        if self._accumulated_session_energy == value:
            return
        self._accumulated_session_energy = value
        self._has_changed = True

    @property
    def accumulated_session_millis(self):
        return self._accumulated_session_millis
    @accumulated_session_millis.setter
    def accumulated_session_millis(self, value):
        if self._accumulated_session_millis == value:
            return
        self._accumulated_session_millis = value
        self._has_changed = True

    @property
    def current_charging_current(self):
        return self._current_charging_current
    @current_charging_current.setter
    def current_charging_current(self, value):
        value = max(0, value / 1000)
        if self._current_charging_current == value:
            return
        self._current_charging_current = value
        self._has_changed = True

    @property
    def current_charging_power(self):
        return self._current_charging_power
    @current_charging_power.setter
    def current_charging_power(self, value):
        if value > 32000:
            value = 0
        if self._current_charging_power == value:
            return
        self._current_charging_power = value
        self._has_changed = True

    @property
    def number_of_phases(self):
        return self._number_of_phases
    @number_of_phases.setter
    def number_of_phases(self, value):
        if self._number_of_phases == value:
            return
        self._number_of_phases = value
        self._has_changed = True

    @property
    def twin_serial(self):
        return self._twin_serial
    @twin_serial.setter
    def twin_serial(self, value):
        if self._twin_serial == value:
            return
        self._twin_serial = value
        self._has_changed = True

    @property
    def has_twin(self):
        return self._twin_serial > 0
    
    @property
    def cable_lock_mode(self):
        return self._cable_lock_mode
    @cable_lock_mode.setter
    def cable_lock_mode(self, value):
        if self._cable_lock_mode == value:
            return
        self._cable_lock_mode = value
        self._has_changed = True

    @property
    def min_current_limit(self):
        return self._min_current_limit
    @min_current_limit.setter
    def min_current_limit(self, value):
        if self._min_current_limit == value:
            return
        self._min_current_limit = value
        self._has_changed = True
