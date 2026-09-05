"""Sensor entity description collections for the sensor platform.

sensor.py only iterates these and instantiates entities; the definitions of
what sensors exist and how they read their state live here.
"""
from typing import Callable, Any
from dataclasses import dataclass

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
    EntityCategory,
)
from homeassistant.components.sensor import (
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription,
)

from .garo import GaroStatus, const, GaroCharger, GaroMeter

AVAILABLE_PHASE_COUNTS = ["1", "2", "3"]


@dataclass(frozen=True, kw_only=True)
class GaroSensorEntityDescription(SensorEntityDescription):
    """Describes a Garo sensor whose state is read from a GaroStatus."""
    get_state: Callable[[GaroStatus], Any]


@dataclass(frozen=True, kw_only=True)
class GaroChargerSensorEntityDescription(SensorEntityDescription):
    """Describes a Garo sensor whose state is read from a GaroCharger."""
    get_state: Callable[[GaroCharger], Any]


@dataclass(frozen=True, kw_only=True)
class GaroMeterSensorEntityDescription(SensorEntityDescription):
    """Describes a Garo sensor whose state is read from a GaroMeter."""
    get_state: Callable[[GaroMeter], Any]


@dataclass(frozen=True, kw_only=True)
class _ChargerFieldSpec:
    """A sensor field shared by every GaroCharger-shaped source (main/twin/slave)."""
    key: str
    name: str
    get_value: Callable[[GaroCharger], Any]
    icon: str | None = None
    options: list[str] | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement: str | None = None
    entity_category: EntityCategory | None = None
    entity_registry_enabled_default: bool = True


# Shared by the main charger's left/right twin sensors and the slave charger sensors -
# all three read from a GaroCharger instance, only the key/name prefix and the
# accessor used to reach that instance differ.
_CHARGER_FIELD_SPECS: list[_ChargerFieldSpec] = [
    _ChargerFieldSpec(
        key="status",
        name="Status",
        options=[opt.value for opt in const.Connector],
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_value=lambda charger: charger.connector.value,
    ),
    _ChargerFieldSpec(
        key="current_charging_current",
        name="Charging Current",
        icon="mdi:flash",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        get_value=lambda charger: charger.current_charging_current,
    ),
    _ChargerFieldSpec(
        key="current_charging_power",
        name="Charging Power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        get_value=lambda charger: charger.current_charging_power,
    ),
    _ChargerFieldSpec(
        key="nr_of_phases",
        name="Number of Phases",
        options=AVAILABLE_PHASE_COUNTS,
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_value=lambda charger: str(charger.number_of_phases),
    ),
    _ChargerFieldSpec(
        key="pilot_level",
        name="Pilot Level",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        get_value=lambda charger: charger.pilot_level,
    ),
    _ChargerFieldSpec(
        key="acc_session_energy",
        name="Session Energy",
        icon="mdi:flash-outline",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        get_value=lambda charger: charger.accumulated_session_energy,
    ),
    _ChargerFieldSpec(
        key="session_time",
        name="Session Time",
        icon="mdi:flash-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        get_value=lambda charger: charger.accumulated_session_millis,
    ),
    _ChargerFieldSpec(
        key="acc_energy",
        name="Total Energy",
        icon="mdi:flash",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        get_value=lambda charger: charger.accumulated_energy / 1000 if charger.accumulated_energy else None,
    ),
    _ChargerFieldSpec(
        key="charge_status",
        name="Charge Status Code",
        icon="mdi:code-tags",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=None,
        get_value=lambda charger: hex(charger.charge_status),
    ),
]


def _build_status_charger_descriptions(
    key_prefix: str, name_prefix: str, get_charger: Callable[[GaroStatus], GaroCharger]
) -> list[GaroSensorEntityDescription]:
    """Build sensor descriptions that read a GaroCharger reached from a GaroStatus (e.g. status.main_charger)."""
    return [
        GaroSensorEntityDescription(
            key=f"{key_prefix}{spec.key}",
            translation_key=f"{key_prefix}{spec.key}",
            name=f"{name_prefix}{spec.name}",
            icon=spec.icon,
            options=spec.options,
            device_class=spec.device_class,
            state_class=spec.state_class,
            native_unit_of_measurement=spec.native_unit_of_measurement,
            entity_category=spec.entity_category,
            entity_registry_enabled_default=spec.entity_registry_enabled_default,
            get_state=lambda status, get_charger=get_charger, spec=spec: spec.get_value(get_charger(status)),
        )
        for spec in _CHARGER_FIELD_SPECS
    ]


def _build_charger_sensor_descriptions() -> list[GaroChargerSensorEntityDescription]:
    """Build sensor descriptions that read directly from a GaroCharger (e.g. a slave charger)."""
    return [
        GaroChargerSensorEntityDescription(
            key=spec.key,
            translation_key=spec.key,
            name=spec.name,
            icon=spec.icon,
            options=spec.options,
            device_class=spec.device_class,
            state_class=spec.state_class,
            native_unit_of_measurement=spec.native_unit_of_measurement,
            entity_category=spec.entity_category,
            entity_registry_enabled_default=spec.entity_registry_enabled_default,
            get_state=spec.get_value,
        )
        for spec in _CHARGER_FIELD_SPECS
    ]


# Sensors read directly off the top-level GaroStatus of a single (non-twin) charger.
MAIN_SENSOR_DESCRIPTIONS: list[GaroSensorEntityDescription] = [
    GaroSensorEntityDescription(
        key="status",
        translation_key="status",
        name="Status",
        options=[opt.value for opt in const.Connector],
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_state=lambda status: status.connector.value,
    ),
    GaroSensorEntityDescription(
        key="current_charging_current",
        translation_key="current_charging_current",
        name="Charging Current",
        icon="mdi:flash",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        get_state=lambda status: status.current_charging_current,
    ),
    GaroSensorEntityDescription(
        key="current_charging_power",
        translation_key="current_charging_power",
        name="Charging Power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        get_state=lambda status: max(status.current_charging_power, 0),
    ),
    GaroSensorEntityDescription(
        key="nr_of_phases",
        translation_key="nr_of_phases",
        name="Number of Phases",
        options=AVAILABLE_PHASE_COUNTS,
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_state=lambda status: str(status.number_of_phases),
    ),
    GaroSensorEntityDescription(
        key="current_limit",
        translation_key="current_limit",
        name="Current Limit",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        get_state=lambda status: status.current_limit,
    ),
    GaroSensorEntityDescription(
        key="pilot_level",
        translation_key="pilot_level",
        name="Pilot Level",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        get_state=lambda status: status.pilot_level,
    ),
    GaroSensorEntityDescription(
        key="acc_session_energy",
        translation_key="acc_session_energy",
        name="Session Energy",
        icon="mdi:flash-outline",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        get_state=lambda status: status.accumulated_session_energy,
    ),
    GaroSensorEntityDescription(
        key="session_time",
        translation_key="session_time",
        name="Session Time",
        icon="mdi:flash-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        get_state=lambda status: status.accumulated_session_millis,
    ),
    GaroSensorEntityDescription(
        key="latest_reading",
        translation_key="latest_reading",
        name="Total Energy",
        icon="mdi:flash",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        get_state=lambda status: status.latest_reading,
    ),
    GaroSensorEntityDescription(
        key="latest_reading_k",
        translation_key="latest_reading_k",
        name="Total Energy kWh",
        icon="mdi:flash",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        get_state=lambda status: status.latest_reading / 1000 if status.latest_reading else None,
    ),
    GaroSensorEntityDescription(
        key="current_temperature",
        translation_key="current_temperature",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        get_state=lambda status: status.current_temperature,
    ),
    GaroSensorEntityDescription(
        key="power_mode",
        translation_key="power_mode",
        name="Power Mode",
        icon="mdi:electric-switch",
        options=[opt.value for opt in const.PowerMode],
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_state=lambda status: status.power_mode.value,
    ),
    GaroSensorEntityDescription(
        key="charge_status",
        translation_key="charge_status",
        name="Charge Status Code",
        icon="mdi:code-tags",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=None,
        get_state=lambda status: hex(status.charge_status),
    ),
]

# Sensors for a twin-outlet main charger: one "left_" set reading status.main_charger,
# one "right_" set reading status.twin_charger.
TWIN_SENSOR_DESCRIPTIONS: list[GaroSensorEntityDescription] = _build_status_charger_descriptions(
    "left_", "Left ", lambda status: status.main_charger
) + _build_status_charger_descriptions(
    "right_", "Right ", lambda status: status.twin_charger
)

# Sensors for a slave charger, reading directly from its GaroCharger.
CHARGER_SENSOR_DESCRIPTIONS: list[GaroChargerSensorEntityDescription] = _build_charger_sensor_descriptions()

SCHEDULE_SENSOR_DESCRIPTION = SensorEntityDescription(
    key="schedule",
    translation_key="schedule",
    icon="mdi:calendar-clock",
    name="Schedule",
    state_class=None,
)


def build_legacy_sensor_description(name: str) -> GaroSensorEntityDescription:
    """The main "mode" sensor description; its name depends on the coordinator's charger name."""
    return GaroSensorEntityDescription(
        key="sensor",
        translation_key="sensor",
        name=name,
        icon="mdi:car-electric",
        options=[opt.value for opt in const.Mode],
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        get_state=lambda status: status.mode.value,
    )


def build_meter_sensor_descriptions(meter_coordinator, is_3_phase: bool = True) -> list[GaroMeterSensorEntityDescription]:
    """Meter sensor descriptions; power readings depend on the specific meter_coordinator's voltage/calculate_power."""
    return [
        GaroMeterSensorEntityDescription(
            key="meter_l1_current",
            translation_key="meter_l1_current",
            name="Current phase L1",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            get_state=lambda meter: meter.l1_current,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_l2_current",
            translation_key="meter_l2_current",
            name="Current phase L2",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            get_state=lambda meter: meter.l2_current,
            entity_registry_enabled_default=is_3_phase,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_l3_current",
            translation_key="meter_l3_current",
            name="Current phase L3",
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            get_state=lambda meter: meter.l3_current,
            entity_registry_enabled_default=is_3_phase,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_l1_power",
            translation_key="meter_l1_power",
            name="Power consumption phase L1",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            get_state=lambda meter: round(meter.l1_current * meter_coordinator.voltage, -1) / 1000 if meter_coordinator.calculate_power else meter.l1_power,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_l2_power",
            translation_key="meter_l2_power",
            name="Power consumption phase L2",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            get_state=lambda meter: round(meter.l2_current * meter_coordinator.voltage, -1) / 1000 if meter_coordinator.calculate_power else meter.l2_power,
            entity_registry_enabled_default=is_3_phase,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_l3_power",
            translation_key="meter_l3_power",
            name="Power consumption phase L3",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            get_state=lambda meter: round(meter.l3_current * meter_coordinator.voltage, -1) / 1000 if meter_coordinator.calculate_power else meter.l3_power,
            entity_registry_enabled_default=is_3_phase,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_power_consumption",
            translation_key="meter_power_consumption",
            name="Power consumption",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            get_state=lambda meter: round((meter.l1_current + meter.l2_current + meter.l3_current) * meter_coordinator.voltage, -1) / 1000 if meter_coordinator.calculate_power else meter.apparent_power,
        ),
        GaroMeterSensorEntityDescription(
            key="meter_accumulated_energy",
            translation_key="meter_accumulated_energy",
            name="Energy consumption (total)",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            get_state=lambda meter: meter.accumulated_energy,
        ),
    ]
