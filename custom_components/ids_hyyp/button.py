"""Support for IDS Hyyp buttons."""
from __future__ import annotations

from typing import Any

from pyhyypapihawkmod.exceptions import HTTPError, HyypApiError
import voluptuous as vol

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import ServiceValidationError

from .const import DATA_COORDINATOR, DOMAIN, SERVICE_TRIGGER_AUTOMATION, ATTR_ARM_CODE, SERVICE_STAY_PROFILE_ARM
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypSiteEntity, HyypPartitionEntity

PARALLEL_UPDATES = 1
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Hyyp button based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    arm_code = entry.options.get(ATTR_ARM_CODE)

    async_add_entities(
        [
            HyypAutomationButton(coordinator, site_id, trigger_id, arm_code)
            for site_id in coordinator.data
            for trigger_id in coordinator.data[site_id]["triggers"]
        ]
    )
    
    async_add_entities(
        [
            HyypStayArmButton(coordinator, site_id, partition_id, stay_profile_id, arm_code)
            for site_id in coordinator.data
            for partition_id in coordinator.data[site_id]["partitions"]
            for stay_profile_id in coordinator.data[site_id]["partitions"][partition_id]["stayProfileIds"]
        ]
    )
    
    async_add_entities(
        [
            HyypRefreshButton(coordinator, site_id)
            for site_id in coordinator.data

        ]
    )
    
    async_add_entities(
        [
            HyypPanicButton(coordinator, site_id, arm_code)
            for site_id in coordinator.data
        ]
    )  
    
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_TRIGGER_AUTOMATION,
        {vol.Required(ATTR_ARM_CODE): str},
        "perform_trigger_automation",
    )
    
    platform.async_register_entity_service(
        SERVICE_STAY_PROFILE_ARM,
        {vol.Required(ATTR_ARM_CODE): str},
        "perform_stay_profile_arm",
    )

class HyypRefreshButton(HyypSiteEntity, ButtonEntity):
    """Representation of a IDS Hyyp entity button."""

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,) -> None:
        """Initialize the button."""
        super().__init__(coordinator, site_id)
        self._attr_name = f"{self.data['name']} Refresh button"
        self._attr_unique_id = f"{self._site_id}_Refresh_button"

   
    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_request_refresh()

class HyypPanicButton(HyypSiteEntity, ButtonEntity):
    """Representation of a IDS Hyyp entity button."""

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        arm_code: str | None,
        ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, site_id)
        self._attr_name = f"{self.data['name']} Panic button"
        self._attr_unique_id = f"{self._site_id}_Panic_button"

        self._arm_code = arm_code
   
    async def async_press(self) -> None:
        """Press the button."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.trigger_alarm,
                self._site_id,
                self._arm_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to call panic  {self._attr_name}") from err

        await self.coordinator.async_request_refresh()
        if (update_ok["status"] != "SUCCESS"):
            raise ServiceValidationError("Could not panic, please check pin code, refresh and try again.")

    
class HyypStayArmButton(HyypPartitionEntity, ButtonEntity):
    """Representation of a IDS Hyyp stay arm entity button. This is to allow for multiple stay arm profiles"""


    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        partition_id: int,
        stay_profile_id: str,
        arm_code: str | None,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, site_id, partition_id)
        self._arm_code = arm_code
        self._stay_profile_id = stay_profile_id
        self._attr_name = f"{self.data['name']} {self.partition_data['name']} Arm: {self.partition_data['stayProfiles'][stay_profile_id]['name'].title()}"
        self._attr_unique_id = f"{self._site_id}_{partition_id}_{stay_profile_id}"

   
    async def async_press(self) -> None:
        """Press the button."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.arm_site,
                self._site_id,
                True,
                self._arm_code,
                self._partition_id,
                self._stay_profile_id,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to arm  {self._attr_name}") from err

        await self.coordinator.async_request_refresh()
        if (update_ok["status"] != "SUCCESS"):
            raise ServiceValidationError("Cannot arm alarm. Check for violated zones or refresh, confirm and try again")
    
    async def perform_stay_profile_arm(self, arm_code: Any = None) -> None:
        """Service to per stay arm if code is not set in options."""
        
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.arm_site,
                self._site_id,
                True,
                arm_code,
                self._partition_id,
                self._stay_profile_id,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to push button {self._attr_name}") from err

        await self.coordinator.async_request_refresh()
        if (update_ok["status"] != "SUCCESS"):
            raise ServiceValidationError("Cannot arm alarm. Check for violated zones or refresh, confirm and try again")



class HyypAutomationButton(HyypSiteEntity, ButtonEntity):
    """Representation of a IDS Hyyp entity button."""


    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        trigger_id: str,
        arm_code: str | None,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, site_id)
        self._arm_code = arm_code
        self._trigger_id = trigger_id
        self._attr_name = f"{self.data['name']} {self.data['triggers'][trigger_id]['name'].title()}"
        self._attr_unique_id = f"{self._site_id}_{trigger_id}"

   
    async def async_press(self) -> None:
        """Press the button."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.trigger_automation,
                self._site_id,
                self._trigger_id,
                self._arm_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to push button {self._attr_name}") from err

        if (update_ok["status"] == "SUCCESS") or (update_ok["status"] == "FAILURE" and (update_ok["error"] is None)):
            await self.coordinator.async_request_refresh()

        else:
            raise HyypApiError(
                f"Failed to push button {self._attr_name} failed with: {update_ok}"
            )
    
    async def perform_trigger_automation(self, arm_code: Any = None) -> None:
        """Service to trigger automation if code is not set in options."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.trigger_automation,
                self._site_id,
                self._trigger_id,
                arm_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to push button {self._attr_name}") from err

        if (update_ok["status"] == "SUCCESS") or (update_ok["status"] == "FAILURE" and (update_ok["error"] is None)):
            await self.coordinator.async_request_refresh()

        else:
            raise HyypApiError(
                f"Failed to push button {self._attr_name} failed with: {update_ok}"
            )
