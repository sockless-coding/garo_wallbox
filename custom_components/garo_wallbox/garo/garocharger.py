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
