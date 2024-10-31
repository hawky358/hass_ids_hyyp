"""Support for IDS Hyyp Alarm."""
from __future__ import annotations

import logging

from pyhyypapihawkmod import HyypClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TIMEOUT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant

from .const import (
    ATTR_ARM_CODE,
    ATTR_BYPASS_CODE,
    CONF_PKG,
    USER_ID,
    DATA_COORDINATOR,
    DEFAULT_TIMEOUT,
    DOMAIN,
    POLLING_TIME,
    DEFAULT_POLL_TIME,
    FCM_CREDENTIALS,
    IMEI,
)
from .coordinator import HyypDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IDS Hyyp from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if not entry.options:
        options = {
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            ATTR_ARM_CODE: None,
            ATTR_BYPASS_CODE: None,
        }

        hass.config_entries.async_update_entry(entry, options=options)
   

    _fcm_credentials = entry.data[FCM_CREDENTIALS]
    hyyp_client = HyypClient(token=entry.data[CONF_TOKEN],
                             pkg=entry.data[CONF_PKG],
                             userid=entry.data[USER_ID],
                             imei=entry.data[IMEI],
                             fcm_credentials=_fcm_credentials,
                             )


    if entry.options.get(POLLING_TIME) is None:
        update_time = int(DEFAULT_POLL_TIME)
    else: 
        update_time = int(entry.options.get(POLLING_TIME))

        
    coordinator = HyypDataUpdateCoordinator(
        hass, entry, api=hyyp_client, api_timeout=DEFAULT_TIMEOUT, update_time=update_time
    )

    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.poll_interval_callback_method(update_time)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)