# Garo Wallbox (EVSE) - HomeAssistant Integration

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&style=for-the-badge&logo=home-assistant&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.garo_wallbox.total)](https://analytics.home-assistant.io/)


This is a custom component to allow control of Garo Wallboxes in [HomeAssistant](https://home-assistant.io).

<p>
    <img src="https://github.com/sockless-coding/garo_wallbox/raw/master/doc/fixed_controls.png" alt="Example controls" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/garo_wallbox/raw/master/doc/fixed_sensors.png" alt="Example sensors" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/garo_wallbox/raw/master/doc/twin_controls.png" alt="Example controls" style="vertical-align: top;max-width:100%" align="top" />
</p>

#### Support Development
- :coffee:&nbsp;&nbsp;[Buy me a coffee](https://www.buymeacoffee.com/sockless)


## Installation

### Install using HACS (recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sockless-coding&repository=garo_wallbox&category=integration)

If you do not have HACS installed yet visit https://hacs.xyz for installation instructions.
In HACS go to the Integrations section, hit the big + at the bottom right and search for **Garo Wallbox**.

### Install manually
Clone or copy this repository and copy the folder `custom_components/garo_wallbox` into `<homeassistant config>/custom_components/garo_wallbox`.

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=garo_wallbox)

Once installed, the Garo Wallbox integration can be configured via the Home Assistant integration interface (**Settings** > **Devices & Services** > **Add Integration** > **Garo Wallbox**), where you enter the IP address or hostname of the device.

Poll intervals for the device and its energy meter can be adjusted afterwards from the integration's **Configure** option.

## Entities

Depending on your wallbox's model and configuration (twin outlets, RFID reader, energy meter, load balancing), the following entities may be created:

- **Sensors** - charging status, current, power, energy and diagnostic values for the wallbox and any connected energy meter
- **Select** - charge mode (`On`/`Off`/`Schedule`) and cable lock mode per outlet
- **Number** - charge current limit, and, when an energy meter is present, mains voltage and load-balancing main fuse rating
- **Switch** - charge limiter enable/disable, RFID authorization (if a reader is present), and calculated power values (diagnostic)
- **Button** - restart the wallbox
- **Update** - reports and installs available firmware updates

## Services

### Set the mode of the EVSE
Service: `garo_wallbox.set_mode`
| Parameter | Description | Example |
| - | - | - |
| entity_id | Name of the entity to change | select.garage_charger |
| mode | The new mode available modes: `On`, `Off`, `Schema` | On |

### Set the charge limit
Service: `garo_wallbox.set_current_limit`
| Parameter | Description | Example |
| - | - | - |
| entity_id | Name of the entity to change | number.garage_charger_current_limit |
| limit | The new limit in Ampere | 10 |

### Add a schedule
Service: `garo_wallbox.add_schedule`
| Parameter | Description | Example |
| - | - | - |
| entity_id | Name of the entity to change | select.garage_charger |
| start | Start time | 08:00 |
| stop | Stop time | 17:00 |
| day_of_the_week | Day of the week: `MONDAY`, `TUESDAY`, `WEDNESDAY`, `THURSDAY`, `FRIDAY`, `SATURDAY`, `SUNDAY` | MONDAY |
| charge_limit | Charge limit for this schedule in Ampere (A) | 16 |

### Update a schedule
Service: `garo_wallbox.set_schedule`
| Parameter | Description | Example |
| - | - | - |
| entity_id | Name of the entity to change | select.garage_charger |
| id | ID of the schedule to update | 1 |
| start | Start time | 08:00 |
| stop | Stop time | 17:00 |
| day_of_the_week | Day of the week: `MONDAY`, `TUESDAY`, `WEDNESDAY`, `THURSDAY`, `FRIDAY`, `SATURDAY`, `SUNDAY` | MONDAY |
| charge_limit | Charge limit for this schedule in Ampere (A) | 16 |

### Remove a schedule
Service: `garo_wallbox.remove_schedule`
| Parameter | Description | Example |
| - | - | - |
| entity_id | Name of the entity to change | select.garage_charger |
| id | ID of the schedule to remove | 1 |


[license-shield]: https://img.shields.io/github/license/sockless-coding/garo_wallbox.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/sockless-coding/garo_wallbox.svg?style=for-the-badge
[releases]: https://github.com/sockless-coding/garo_wallbox/releases
