from . import utils

class GaroLBConfig:
    """Holds load-balancing settings from the lbconfig endpoint."""

    def __init__(self, json = None):
        self._fuse = 0
        self._fuse101 = 0
        self._master_load_balanced = False
        self._slaves = []

        self._has_changed = False
        self.load(json)

    def load(self, json = None) -> bool:
        self._has_changed = False
        if not json:
            return False

        self.fuse = utils.read_value(json, 'loadBalancingFuse', self._fuse)
        self.fuse101 = utils.read_value(json, 'loadBalancingFuse101', self._fuse101)
        self.master_load_balanced = bool(utils.read_value(
            json, 'masterLoadBalanced', self._master_load_balanced))
        self.slaves = utils.read_value(json, 'slaves', self._slaves)

        return self._has_changed

    @property
    def has_changed(self):
        return self._has_changed

    @property
    def enabled(self):
        """True when the master and every listed charger use load balancing."""
        return self.master_load_balanced and all(
            bool(slave.get('loadBalanced', False)) for slave in self.slaves)

    @property
    def master_load_balanced(self):
        return self._master_load_balanced
    @master_load_balanced.setter
    def master_load_balanced(self, value):
        if self._master_load_balanced == value:
            return
        self._master_load_balanced = value
        self._has_changed = True

    @property
    def slaves(self):
        return self._slaves
    @slaves.setter
    def slaves(self, value):
        if self._slaves == value:
            return
        self._slaves = value
        self._has_changed = True

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
    def fuse101(self):
        """Main fuse current limit (A) for the LB Meter 101 group."""
        return self._fuse101
    @fuse101.setter
    def fuse101(self, value):
        if self._fuse101 == value:
            return
        self._fuse101 = value
        self._has_changed = True
