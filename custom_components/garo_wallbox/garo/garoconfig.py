from . import const, utils, GaroCharger

class GaroConfig:

    def __init__(self, json):
        self.max_charge_current = utils.read_value(json,'maxChargeCurrent', 0)
        self.product_id = int(utils.read_value(json, 'productId', '0'))
        self.product = const.PRODUCT_MAP[self.product_id] if self.product_id in const.PRODUCT_MAP else const.GaroProductInfo('Unknown')
        self.serial_number = utils.read_value(json,'serialNumber', 0)
        self.firmware_version = utils.read_value(json, 'firmwareVersion', 0)
        self.firmware_revision = utils.read_value(json, 'firmwareRevision', 0)
        self.factory_charge_limit = utils.read_value(json, 'factoryChargeLimit', 0)
        self.charge_limit_enabled = utils.read_value(json,'reducedIntervalsEnabled', False)
        self.switch_charge_limit = utils.read_value(json,'switchChargeLimit', 0)
        self.software_version = utils.read_value(json,'softwareVersion', 0)
        self.package_version = utils.read_value(json, 'packageVersion', '0')
        self.twin_serial = utils.read_value(json, 'twinSerial', 0)
        self.standalone = bool(utils.read_value(json,'standalone', 'false'))
        slaves = utils.read_value(json, 'slaveList', [])
        self.devices: list[GaroCharger] = [GaroCharger(slave) for slave in slaves]

    @property
    def has_twin(self):
        return self.twin_serial > 0
    
    @property
    def has_outlet(self):
        return self.product.has_outlet and (self.firmware_version > 7 or (self.firmware_version == 7 and self.firmware_revision >= 5))

