"""Config flow."""
from __future__ import annotations

import logging
from typing import Any

from pyhyypapihawkmod.client import HyypClient
from pyhyypapihawkmod.constants import DEFAULT_TIMEOUT
from pyhyypapihawkmod.exceptions import HTTPError, HyypApiError, InvalidURL
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TIMEOUT, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

from .const import (
    ATTR_ARM_CODE,
    ATTR_BYPASS_CODE,
    CONF_PKG,
    USER_ID,
    DOMAIN,
    PKG_ADT_SECURE_HOME,
    PKG_IDS_HYYP,
    PKG_ADT_ALIAS,
    PGK_IDS_HYYP_ALIAS,
    POLLING_TIME,
    DEFAULT_POLL_TIME,
    POLLING_TIME_NEVER_POLL,
    POLLING_TIME_24_HOURS,
    IMEI,
    FCM_CREDENTIALS
)

_LOGGER = logging.getLogger(__name__)
DEFAULT_OPTIONS = {
    CONF_TIMEOUT: DEFAULT_TIMEOUT,
}

    
    
def _validate_and_create_auth(data: dict) -> dict[str, Any]:
    """Try to login to IDS Hyyp account and return token."""
    # Verify cloud credentials by attempting a login request with username and password.
    # Return login token.

    imei = str(HyypClient().generate_imei())
    hyyp_client = HyypClient(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        pkg=data[CONF_PKG],
        imei=imei
    )
    hyyp_token = hyyp_client.login()

    return {CONF_TOKEN: hyyp_token[CONF_TOKEN], 
            CONF_PKG: data[CONF_PKG],
            USER_ID: hyyp_token["user"]["id"],
            IMEI: imei,
            FCM_CREDENTIALS: None
            }


class HyypConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hyyp."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> HyypOptionsFlowHandler:
        """Get the options flow for this handler."""
        return HyypOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""

        errors = {}
        token_data = {}

        if user_input is not None:

            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()

            try:
                token_data = await self.hass.async_add_executor_job(
                    _validate_and_create_auth, user_input
                )
            
            except InvalidURL:
                errors["base"] = "invalid_host"

            except HTTPError:
                errors["base"] = "cannot_connect"

            except HyypApiError:
                errors["base"] = "invalid_auth"

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")

            else:
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=token_data,
                    options=DEFAULT_OPTIONS,
                )    

        data_schema = {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_PKG, default=PKG_IDS_HYYP): selector({
                "select": {
                    "options": [
        
                        {
                            "label" : PKG_ADT_ALIAS,
                            "value" : PKG_ADT_SECURE_HOME
                            
                        },          
                        {
                            "label" : PGK_IDS_HYYP_ALIAS,
                            "value" : PKG_IDS_HYYP      
                        },              
                        ],
                        }
                }),
         
        }
                
        data_schema=vol.Schema(data_schema)
        
        EventCategory = {"1": "Emergency", "2": "User", "3": "Trouble", "4": "Information"}
        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )


class HyypOptionsFlowHandler(OptionsFlow):
    """Handle Hyyp client options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Hyyp options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        
        options = vol.Schema(
            {
                vol.Optional(ATTR_ARM_CODE): str,
                vol.Optional(ATTR_BYPASS_CODE): str,                   
                vol.Optional(
                    POLLING_TIME,
                    default=self.config_entry.options.get(POLLING_TIME, str(DEFAULT_POLL_TIME))
                    ): 
                        selector({
                            "select": {
                                "options": [
                                    {
                                        "label" : "30 Secs (Default)",
                                        "value" : str(DEFAULT_POLL_TIME)
                                        
                                    },       

                                    {   
                                        "label" : "24 Hours (For use with GSM Modules)",
                                        "value" : str(POLLING_TIME_24_HOURS)
                                        
                                    },      
                                    {
                                        "label" : "Never* (For use with GSM Modules)",
                                        "value" : str(POLLING_TIME_NEVER_POLL)
                                        
                                    },               
                                    ],
                                "mode": "dropdown",
                                    }
                        }),
        
            }
        )
        

        return self.async_show_form(step_id="init", data_schema=options)
