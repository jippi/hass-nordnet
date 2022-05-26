from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PLATFORM

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    _LOGGER.debug(f"async_setup_entry called for entry '{entry.title}' (sensor.py)")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for holding in coordinator.holdings():
        sensor = NordnetStock(dict(holding), coordinator)
        sensors.append(sensor)

        _LOGGER.debug(f"Created sensor '{sensor.unique_id}'")

    async_add_entities(sensors, True)


class NordnetStock(CoordinatorEntity, SensorEntity):

    def __init__(self, holding, coordinator):
        super().__init__(coordinator)

        self._attributes = self._remap(holding)
        self._name = f"Stock price for {self._attributes['instrument']['name']} ({self._attributes['instrument']['symbol']})"
        self._unique_id = "nordnet_stock_{}".format(self._attributes['instrument']['symbol'].replace(' ', '_')).lower()
        self._symbol = self._attributes['instrument']['symbol']

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._attributes['account_market_value']

    @property
    def state_class(self):
        return "measurement"

    @property
    def extra_state_attributes(self):
        return dict(self._attributes)

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.account_currency().upper()

    @property
    def device_class(self):
        return "monetary"

    @property
    def native_value(self):
        return "float"

    @property
    def icon(self):
        return "mdi:cash"

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Called by the coordinater every time there are new data fetched from Nordnet API
        """

        new = self.coordinator.holding_for_symbol(self._symbol)
        if new is None:
            _LOGGER.error(f"Could not find any new data for {self.unique_id}")
            return

        self._attributes = self._remap(new)
        self.async_write_ha_state()

    def _remap(self, input) -> dict:
        """
        Change the raw Nordnet API response into a more flat dictionary where possible
        to ease use in templates, and allow the 'datadog' integration to emit metrics
        for all the numeric values automatically

        Also adds some basic ROI attributes that are kinda best-effort based on the
        data made available via the API response
        """

        # the native currency of the position (e.g. USD, NOK, SEK)
        # not to be confused with the account currency
        ncur = input['main_market_price']['currency'].lower()

        # make a copy before modifying it
        input = dict(input)
        input['position_currency'] = ncur
        input['account_currency'] = self.coordinator.account_currency()

        # (account) market value
        input['account_market_value'] = input['market_value_acc']['value']
        input['position_market_value'] = input['market_value']['value']
        del input['market_value_acc']
        del input['market_value']

        # acquisition price
        input['account_acquisition_price'] = input['acq_price_acc']['value']
        input['position_acquisition_price'] = input['acq_price']['value']
        del input['acq_price_acc']
        del input['acq_price']

        # morning price
        input['position_morning_price'] = input['morning_price']['value']
        del input['morning_price']

        # main_market_price
        input['position_market_price'] = input['main_market_price']['value']
        del input['main_market_price']

        # rename qty field
        input['quantity'] = input['qty']
        del input['qty']

        # compute Return On Investment (in account currency)
        input['account_roi'] = input['account_market_value'] - (input['quantity'] * input['account_acquisition_price'])

        # compute Return On Investment %
        input['account_roi_percent'] = (input['position_market_price'] - input['position_acquisition_price']) / input['position_acquisition_price'] * 100

        input['account_number'] = input['accno']
        del input['accno']

        input['account_id'] = input['accid']
        del input['accid']

        # cleanup things we don't care about
        del input['is_custom_gav']
        del input['margin_percent']
        del input['pawn_percent']

        return input
