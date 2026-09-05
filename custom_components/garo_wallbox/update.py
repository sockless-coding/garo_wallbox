from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityDescription,
    UpdateDeviceClass,
    UpdateEntityFeature,
)

from .coordinator import GaroDeviceCoordinator
from . import GaroConfigEntry

_LOGGER = logging.getLogger(__name__)

# The wallbox checks its cloud service for new firmware; there is no need to poll this often.
SCAN_INTERVAL = timedelta(hours=12)


async def async_setup_entry(hass: HomeAssistant, entry: GaroConfigEntry, async_add_entities):
    """Set up using config_entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([GaroUpdateEntity(coordinator, entry)], True)


class GaroUpdateEntity(UpdateEntity):
    """Reports and installs available Garo Wallbox firmware updates."""

    _attr_has_entity_name = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(self, coordinator: GaroDeviceCoordinator, entry) -> None:
        self.config_entry = entry
        self._coordinator = coordinator
        self.entity_description = UpdateEntityDescription(
            key="firmware",
            translation_key="firmware",
            name="Firmware",
        )
        self._attr_unique_id = f"{coordinator.device_id}-firmware"
        self._attr_device_info = coordinator.device_info
        self._attr_installed_version = str(coordinator.config.software_version)
        self._latest_url: str | None = None

    async def async_update(self) -> None:
        """Check the wallbox's cloud service for a newer firmware version."""
        self._attr_installed_version = str(self._coordinator.config.software_version)
        try:
            data = await self._coordinator.api_client.async_get_update_info()
        except Exception as e:
            _LOGGER.debug("Failed to check for firmware update: %s", e)
            return
        latest_version = int(data.get('latest_version', -1))
        if latest_version < 0:
            # -1: chargebox has no internet connectivity, -2: chargebox clock is out of sync
            self._latest_url = None
            self._attr_latest_version = self._attr_installed_version
            return
        self._latest_url = data.get('url')
        self._attr_latest_version = str(latest_version)

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Trigger the wallbox to download and install the new firmware."""
        if not self._latest_url:
            raise HomeAssistantError("No firmware update package is available")
        await self._coordinator.api_client.async_install_update(self._latest_url, self._attr_latest_version)
