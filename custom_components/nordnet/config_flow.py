from __future__ import annotations

import logging
import copy
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow,  CONN_CLASS_CLOUD_POLL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import selector

from .const import (DEFAULT_ACCOUNT_ID, DEFAULT_SESSION_LIFETIME,
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
        vol.Required("session_lifetime", default=DEFAULT_SESSION_LIFETIME): selector.DurationSelector(),
    }
)


async def validate_connection(hass: HomeAssistant, user_input: dict):
    c = Coordinator(hass, Coordinator.map_config(user_input))
    await c.test()


class NordnetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 3

    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry,) -> NordnetOptionsFlowHandler:
        return NordnetOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step."""
        errors = {}

        if user_input is not None:
            try:
                await validate_connection(self.hass, user_input)
            except ValueError:
                errors["query"] = "query_invalid"

            if not errors:
                return self.async_create_entry(title=user_input['username'], data={}, options=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors,)


class NordnetOptionsFlowHandler(OptionsFlow):

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Default schema
        schema = DATA_SCHEMA

        errors = {}
        if user_input is not None:
            try:
                await validate_connection(self.hass, user_input)
            except ValueError:
                errors["query"] = "query_invalid"
            else:
                return self.async_create_entry(title=user_input['username'], data=user_input)

        # ensure default values are injected into the data schema when showing it
        schema = self._enrich_schema(DATA_SCHEMA, user_input or self.config_entry.options)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    def _enrich_schema(self, data_schema: vol.Schema, user_input: dict) -> vol.Schema:
        """
        Set 'suggested_value' based on existing option values in the config entry
        so the options form has currently configured values
        """
        schema = {}
        for key, val in data_schema.options.items():
            new_key = key

            if key in user_input and isinstance(key, vol.Marker):
                # Copy the marker to not modify the flow schema
                new_key = copy.copy(key)
                new_key.description = {"suggested_value": user_input[key]}

            schema[new_key] = val

        return vol.Schema(schema)
