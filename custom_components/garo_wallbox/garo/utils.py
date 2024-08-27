import logging

_LOGGER = logging.getLogger(__name__)

def read_enum(json, key, type, default_value):
    if key not in json:
        return default_value
    try:
        return type(json[key])
    except Exception as es:
        _LOGGER.warn("Error reading property '%s' with value '%s'", key, json[key], exc_info= es)
    return default_value

def read_value(json, key, default_value):    
    return json[key] if key in json else default_value