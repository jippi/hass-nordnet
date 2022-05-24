from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler, SchemaFlowFormStep, SchemaFlowMenuStep)

from .const import (DEFAULT_ACCOUNT_ID, DEFAULT_SESSION_LIFETIME,
                    DEFAULT_TRADING_START_TIME, DEFAULT_TRADING_STOP_TIME,
                    DEFAULT_UPDATE_INTERVAL, DOMAIN, PLATFORM)

_LOGGER = logging.getLogger(__name__)

# See https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/selector.py
OPTIONS_SCHEMA = vol.Schema(
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

CONFIG_SCHEMA = vol.Schema(
    {

    }
).extend(OPTIONS_SCHEMA.schema)

CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA)
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):

    VERSION = 3

    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    config_flow = CONFIG_FLOW

    options_flow = OPTIONS_FLOW

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """
        Generate default entry title
        """

        return options['username']
