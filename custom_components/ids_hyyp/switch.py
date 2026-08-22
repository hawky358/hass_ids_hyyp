"""Support for IDS Hyyp Switches."""
from __future__ import annotations

from typing import Any

from pyhyypapihawkmod.exceptions import HTTPError, HyypApiError
import voluptuous as vol

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo

from .const import ATTR_ARM_CODE, ATTR_BYPASS_CODE, DATA_COORDINATOR, DOMAIN, SERVICE_BYPASS_ZONE
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypSiteEntity, HyypPartitionEntity

PARALLEL_UPDATES = 1
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Hyyp switch based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    bypass_code = entry.options.get(ATTR_BYPASS_CODE)
    arm_code = entry.options.get(ATTR_ARM_CODE)

    async_add_entities(
        [
            HyypBypassSwitch(coordinator, site_id, partition_id, zone_id, bypass_code)
            for site_id in coordinator.data
            for partition_id in coordinator.data[site_id]["partitions"]
            for zone_id in coordinator.data[site_id]["partitions"][partition_id][
                "zones"
            ]
        ]   
    )
    
    
    async_add_entities(
        [
            HyypAutomationSwitch(coordinator, site_id, trigger_id, arm_code)
            for site_id in coordinator.data
            for trigger_id in coordinator.data[site_id]["triggers"]
            if coordinator.data[site_id]["triggers"][trigger_id]["type"] == "switch"
        ]   
    )

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_BYPASS_ZONE,
        {vol.Required(ATTR_BYPASS_CODE): str},
        "perform_zone_bypass_code",
    )


class HyypBypassSwitch(HyypPartitionEntity, SwitchEntity):
    """Representation of a IDS Hyyp entity Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        partition_id: int,
        zone_id: str,
        bypass_code: str | None,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, site_id, partition_id)
        self._bypass_code = bypass_code
        self._zone_id = zone_id
        self._sensor_name = f"{self.partition_data['zones'][zone_id]['name'].title()}"
        self._attr_name = self._sensor_name
        self._attr_unique_id = f"{self._site_id}_{partition_id}_{zone_id}"

    @property
    def available(self) -> bool:
        """Check if device is reporting online from api."""
        return bool(self.data["isOnline"])


    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return not self.partition_data["zones"][self._zone_id]["bypassed"]
    
    @property
    def extra_state_attributes(self):
        
        violated = False
        tampered = False
        triggered = False
        stay_bypassed = False
        short_name = self._sensor_name
        if "openviolated" in self.partition_data["zones"][self._zone_id]:
            violated = bool(self.partition_data["zones"][self._zone_id]["openviolated"])
        if "tampered"  in self.partition_data["zones"][self._zone_id]:
            tampered = bool(self.partition_data["zones"][self._zone_id]["tampered"])
        if "stay_bypassed" in self.partition_data["zones"][self._zone_id]:
            stay_bypassed = bool(self.partition_data["zones"][self._zone_id]["stay_bypassed"])
        if "triggered" in self.partition_data["zones"][self._zone_id]:
            triggered = bool(self.partition_data["zones"][self._zone_id]["triggered"])
        state = {"violated" : violated,
                 "tampered" : tampered,
                 "triggered" : triggered,
                 "stay_bypassed" : stay_bypassed,
                 "short_name" : short_name
                 }
        return state
    



    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch entity on."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._zone_id,
                self._partition_id,
                0,
                self._bypass_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise ServiceValidationError(f"Zone: {self._attr_name} - IDS Server did not verify successful zone un-bypass. Please refresh and confirm or try again.")

        else:
            raise HyypApiError(
                f"Failed to bypass zone {self._attr_name} failed with: {update_ok}"
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch entity off."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._zone_id,
                self._partition_id,
                0,
                self._bypass_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Failed to turn on switch {self._attr_name}") from err

        
        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise ServiceValidationError(f"Zone: {self._attr_name} - IDS Server did not verify successful zone bypass. Please refresh and confirm or try again.")

        else:
            raise HyypApiError(
                f"Disable bypass on zone {self._attr_name} failed with: {update_ok}"
            )

    async def perform_zone_bypass_code(self, code: Any = None) -> None:
        """Service to bypass zone if code is not set in options."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._zone_id,
                self._partition_id,
                0,
                code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()
            
        elif update_ok["status"] == "PENDING":
            raise ServiceValidationError(f"Zone: {self._attr_name} - IDS Server did not verify successful zone bypass. Please refresh and confirm or try again.")

        else:
            raise HyypApiError(
                f"Disable bypass on zone {self._attr_name} failed with: {update_ok}"
            )


class HyypAutomationSwitch(HyypSiteEntity, SwitchEntity):
    """Representation of a IDS Hyyp entity Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

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
        self._attr_name = f"{self.data['name']} {self.data['triggers'][trigger_id]['name'].title()} switch"
        self._attr_unique_id = f"{self._site_id}_{trigger_id}_switch"

    @property
    def available(self) -> bool:
        """Check if device is reporting online from api."""
        return bool(self.data["isOnline"])

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self.data["triggers"][self._trigger_id]["onoff"]
    
    @property
    def extra_state_attributes(self):
        
        type = "pulse"
        if "type" in self.data["triggers"][self._trigger_id]:
            type = self.data["triggers"][self._trigger_id]["type"]
        state = {"type" : type,
                 "short_name" : self._attr_name,
                 }
        return state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch entity on."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.trigger_automation,
                self._site_id,
                self._trigger_id,
                self._arm_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise ServiceValidationError(f"Zone: {self._attr_name} - IDS Server did not verify successful triggering of automation. Please refresh and confirm or try again.")

        else:
            raise HyypApiError(
                f"Failed to bypass zone {self._attr_name} failed with: {update_ok}"
            )


    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch entity off."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.trigger_automation,
                self._site_id,
                self._trigger_id,
                self._arm_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn off switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise ServiceValidationError(f"Zone: {self._attr_name} - IDS Server did not verify successful triggering of automation. Please refresh and confirm or try again.")

        else:
            raise HyypApiError(
                f"Failed to bypass zone {self._attr_name} failed with: {update_ok}"
            )

