from __future__ import annotations

import copy
import json
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (CONN_CLASS_CLOUD_POLL, ConfigEntry,
                                          ConfigFlow, OptionsFlow)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (DEFAULT_ACCOUNT_ID,
                    DEFAULT_TRADING_START_TIME, DEFAULT_TRADING_STOP_TIME,
                    DEFAULT_UPDATE_INTERVAL, DOMAIN, PLATFORM)
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)

# See https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/selector.py
DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): selector.TextSelector(),
        vol.Required("password"): selector.TextSelector({'type': 'password'}),
        vol.Required("account_id", default=DEFAULT_ACCOUNT_ID): selector.NumberSelector({'mode': 'box', 'step': 1}),
        vol.Required("trading_start_time", default=DEFAULT_TRADING_START_TIME): selector.TimeSelector(),
        vol.Required("trading_stop_time", default=DEFAULT_TRADING_STOP_TIME): selector.TimeSelector(),
        vol.Required("update_interval", default=DEFAULT_UPDATE_INTERVAL): selector.DurationSelector(),
    }
)


async def get_account_details(hass: HomeAssistant, user_input: dict) -> tuple[dict, dict]:
    """
    Validate connection and credentials to Nordnet API when creating or
    updating a configuration entry
    """
    try:
        c = Coordinator(hass, Coordinator.map_config(user_input))
        return await c.get_account_details(), None

    except aiohttp.ClientConnectionError as ex:
        _LOGGER.error(f'ClientConnectorError: {str(ex)}')
        return None, {'username': 'connection_error'}

    except aiohttp.ClientResponseError as ex:
        _LOGGER.error(f'HTTPError: {str(ex)}')
        if ex.status > 400 and ex.status < 500:
            return None, {'username': 'auth_error'}

        return None, {'username': 'http_error'}

    except Exception as ex:
        _LOGGER.error(f'Generic Exception: {str(ex)}')
        return None, {'username': 'unknown'}


def enrich_schema(user_input: dict) -> vol.Schema:
    if user_input is None:
        return DATA_SCHEMA

    """
    Set 'suggested_value' based on existing option values in the config entry
    so the options form has currently configured values
    """
    schema = {}
    for key, val in DATA_SCHEMA.schema.items():
        new_key = key

        if key in user_input and isinstance(key, vol.Marker):
            # Copy the marker to not modify the flow schema
            new_key = copy.copy(key)
            new_key.description = {"suggested_value": user_input[key]}

        schema[new_key] = val

    return vol.Schema(schema)


class NordnetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 4

    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry,) -> NordnetOptionsFlowHandler:
        return NordnetOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step."""
        errors = {}

        if user_input is not None:
            account_info, errors = await get_account_details(self.hass, user_input)
            if not errors:
                user_input['account_currency'] = account_info['account_currency'].lower()
                return self.async_create_entry(title=user_input['username'], data={}, options=user_input)

        return self.async_show_form(step_id="user", data_schema=enrich_schema(user_input), errors=errors)


class NordnetOptionsFlowHandler(OptionsFlow):

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}

        if user_input is not None:
            account_info, errors = await get_account_details(self.hass, user_input)
            if not errors:
                user_input['account_currency'] = account_info['account_currency'].lower()
                return self.async_create_entry(title=user_input['username'], data=user_input)

        schema = enrich_schema(user_input or self.config_entry.options)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
