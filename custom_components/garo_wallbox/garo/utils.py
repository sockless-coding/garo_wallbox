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

def read_bool(json, key, default_value: bool) -> bool:
    """Read a value that may be a JSON bool or a "true"/"false" string."""
    if key not in json or json[key] is None:
        return default_value
    value = json[key]
    if isinstance(value, str):
        return value.strip().lower() == 'true'
    return bool(value)