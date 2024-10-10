"""Provides the DataUpdateCoordinator."""
from datetime import timedelta
import logging
from typing import Any
import json
import time

from async_timeout import timeout
from pyhyypapihawkmod.client import HyypClient
from pyhyypapihawkmod.exceptions import HTTPError, HyypApiError, InvalidURL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HyypDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching IDSHyyp data."""

    def __init__(
        self, hass: HomeAssistant, *, api: HyypClient, api_timeout: int, update_time: int = 30
    ) -> None:
        """Initialize global IDS Hyyp data updater."""
        self.hyyp_client = api
        self._api_timeout = api_timeout
        update_interval = timedelta(seconds=update_time)
        self.push_notification_entity_callback_methods = []
        self.poll_interval_callback_method = None
        self._arm_fail_cause_callback_method = None
        
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self.hyyp_client.register_generic_callback_to_hass(callback=self._generic_callback_for_data_from_api)
        hass.async_add_executor_job(self._init_FCM_notifications)
        
    async def _async_update_data(self) -> dict[Any, Any]:
        """Fetch data from IDS Hyyp."""
 
        try:
            async with timeout(self._api_timeout):
                return await self.hass.async_add_executor_job(
                    self.hyyp_client.load_alarm_infos
                )

        except (InvalidURL, HTTPError, HyypApiError) as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error
    
    def _update_fcm_data(self, data):       
        if data == "restart_push_receiver":     

            self.hyyp_client.initialize_fcm_notification_listener(callback=self._update_fcm_data, restart=True)
            return

        
        try:
            msgtype = data['notification']['data']['message']
            if msgtype.find("PUSH") == 0:
                self._update_push_notification_entity(data=data)
                return
            if msgtype.find("ERROR") == 0:
                self._update_fail_cause_entity(data=data)
                return
        except KeyError:
            pass
    
    
    def _update_push_notification_entity(self, data):

        try:
            short_json = data["notification"]["notification"]
            if isinstance(short_json, str):
                short_json = json.loads(short_json)
            short_json["timestamp"] = time.time() 
            message = json.dumps(short_json)        
            for callback in self.push_notification_entity_callback_methods:
                callback(data=message)
        except KeyError:
            return
        
    def _update_fail_cause_entity(self, data):
        try:
            short_json = data["notification"]["notification"]
            if isinstance(short_json, str):
                short_json = json.loads(short_json)
            short_json["timestamp"] = time.time() 
            message = json.dumps(short_json)        
            self._arm_fail_cause_callback_method(message)
        except KeyError:
            return
        
    def _register_callback_for_push_notification_entity(self, callback):
        self.push_notification_entity_callback_methods.append(callback)     
    
    def _register_poll_inverval_update_callback(self, callback):
        self.poll_interval_callback_method = callback
        
    def _register_arm_fail_cause_callback(self, callback):
        self._arm_fail_cause_callback_method = callback       
        

    def _generic_callback_for_data_from_api(self, data):
        if "arm_fail_cause" in data:
            short_json = data["arm_fail_cause"]
            if isinstance(short_json, str):
                short_json = json.loads(short_json)
            short_json["timestamp"] = time.time() 
            message = json.dumps(short_json)          
            self._arm_fail_cause_callback_method(message)
            return
        
        if "fcm_data" in data:
            self._update_fcm_data(data=data["fcm_data"])
        

    def _init_FCM_notifications(self):    
        self.hyyp_client.initialize_fcm_notification_listener(callback=self._update_fcm_data)
        
