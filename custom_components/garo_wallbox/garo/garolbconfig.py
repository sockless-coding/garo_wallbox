from . import utils

class GaroLBConfig:
    """Holds the main fuse/power subscription load balancing settings (lbconfig endpoint)."""

    def __init__(self, json = None):
        self._fuse = 0
        self._power = 0
        self._fuse101 = 0
        self._power101 = 0

        self._has_changed = False
        self.load(json)

    def load(self, json = None) -> bool:
        self._has_changed = False
        if not json:
            return False

        self.fuse = utils.read_value(json, 'loadBalancingFuse', self._fuse)
        self.power = utils.read_value(json, 'loadBalancingPower', self._power)
        self.fuse101 = utils.read_value(json, 'loadBalancingFuse101', self._fuse101)
        self.power101 = utils.read_value(json, 'loadBalancingPower101', self._power101)

        return self._has_changed

    @property
    def has_changed(self):
        return self._has_changed

    @property
    def fuse(self):
        """Main fuse current limit (A) for the LB Meter 100 group."""
        return self._fuse
    @fuse.setter
    def fuse(self, value):
        if self._fuse == value:
            return
        self._fuse = value
        self._has_changed = True

    @property
    def power(self):
        """Power subscription limit (kW) for the LB Meter 100 group."""
        return self._power
    @power.setter
    def power(self, value):
        if self._power == value:
            return
        self._power = value
        self._has_changed = True

    @property
    def fuse101(self):
        """Main fuse current limit (A) for the LB Meter 101 group."""
        return self._fuse101
    @fuse101.setter
    def fuse101(self, value):
        if self._fuse101 == value:
            return
        self._fuse101 = value
        self._has_changed = True

    @property
    def power101(self):
        """Power subscription limit (kW) for the LB Meter 101 group."""
        return self._power101
    @power101.setter
    def power101(self, value):
        if self._power101 == value:
            return
        self._power101 = value
        self._has_changed = True
