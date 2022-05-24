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
        return self._attributes['market_value_acc_dkk']

    @property
    def state_class(self):
        return "measurement"

    @property
    def extra_state_attributes(self):
        return dict(self._attributes)

    @property
    def native_unit_of_measurement(self):
        return "DKK"

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

        # make a copy before modifying it
        input = dict(input)

        ncur = input['main_market_price']['currency'].lower()

        # remap market_value_acc[currency,value] to flat value since its always in DKK
        input['market_value_acc_dkk'] = input['market_value_acc']['value']
        del input['market_value_acc']

        # remap acq_price_acc[currency,value] to flat value since its always in DKK
        input['acq_price_acc_dkk'] = input['acq_price_acc']['value']
        del input['acq_price_acc']

        # remap acq_price to currency specific field
        input[f'acq_price_{ncur}'] = input['acq_price']['value']
        input[f'acq_price_native'] = input['acq_price']['value']
        del input['acq_price']

        # remap market_value to currency specific field
        input[f'market_value_{ncur}'] = input['market_value']['value']
        input[f'market_value_native'] = input['market_value']['value']
        del input['market_value']

        # remap morning_price to currency specific field
        input[f'morning_price_{ncur}'] = input['morning_price']['value']
        input[f'morning_price_native'] = input['morning_price']['value']
        del input['morning_price']

        # remap main_market_price to currency specific field
        input[f'main_market_price_{ncur}'] = input['main_market_price']['value']
        input[f'main_market_price_native'] = input['main_market_price']['value']
        del input['main_market_price']

        # rename qty field
        input['quantity'] = input['qty']
        del input['qty']

        # compute Return On Investment (in DKK)
        input['roi_dkk'] = input['market_value_acc_dkk'] - (input['quantity'] * input['acq_price_acc_dkk'])

        # compute Return On Investment %
        input['roi_percent'] = (input['main_market_price_native'] - input['acq_price_native']) / input['acq_price_native'] * 100

        # cleanup things we don't care about
        del input['is_custom_gav']
        del input['margin_percent']
        del input['pawn_percent']

        return input
