from datetime import time, datetime
import json

from . import const, utils

class GaroSchema:

    def __init__(self, json = None):

        self._id = -1
        self._start = time(0,0)
        self._stop = time(0,0)
        self._day_of_the_week = const.SchemaDayOfWeek.MONDAY
        self._charge_limit = 0

        self._has_changed = False
        self.load(json)

    def load(self, json):
        if not json:
            return False
        self._has_changed = False
        if self._id < 1:
            self._id = utils.read_value(json, 'schemaId', -1)
            self._has_changed = True
        self.start = datetime.strptime(utils.read_value(json, 'start', self._start.strftime("%H:%M:%S")), "%H:%M:%S").time()
        self.stop = datetime.strptime(utils.read_value(json, 'stop', self._stop.strftime("%H:%M:%S")), "%H:%M:%S").time()
        self.day_of_the_week = utils.read_enum(json, 'weekday', const.SchemaDayOfWeek, self._day_of_the_week)
        self.charge_limit = utils.read_value(json, 'chargeLimit', self._charge_limit)
        return self._has_changed
        

    @property
    def id(self):
        if self._id < 1:
            raise ValueError("Invalid ID")
        return self._id
    
    @property
    def start(self):
        return self._start
    @start.setter
    def start(self, value):
        if self._start == value:
            return
        self._start = value
        self._has_changed = True

    @property
    def stop(self):
        return self._stop
    @stop.setter
    def stop(self, value):
        if self._stop == value:
            return
        self._stop = value
        self._has_changed = True

    @property
    def day_of_the_week(self):
        return self._day_of_the_week
    @day_of_the_week.setter
    def day_of_the_week(self, value):
        if self._day_of_the_week == value:
            return
        self._day_of_the_week = value
        self._has_changed = True

    @property
    def charge_limit(self):
        return self._charge_limit
    @charge_limit.setter
    def charge_limit(self, value):
        if self.charge_limit == value:
            return
        self._charge_limit = value
        self._has_changed = True

    @property
    def has_changed(self):
        return self._has_changed
    

    