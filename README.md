# Nordnet for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

The `nordnet` component is a Home Assistant custom component for fetching your Nordnet holdings (investments) from their API and expose them as sensors.

## Installation

### Manual Installation

  1. Copy `nordnet` folder into your custom_components folder in your hass configuration directory.
  2. Restart Home Assistant.
  3. Configure `Nordnet` through Configuration -> Integrations -> Add Integration.

### Installation with HACS (Home Assistant Community Store)

  1. Ensure that [HACS](https://hacs.xyz/) is installed.
  2. Search for and install the `nordnet` integration through HACS.
  3. Restart Home Assistant.
  4. Configure `Nordnet` through Configuration -> Integrations -> Add Integration.


## Configuration

### Username & Password

Pretty straight forward, the credentials used to login to your Nordnet account.

Sadly Nordnet do not have a API token system or similar for private customers (unless you pay them BIG $$$!), so the only way to have the integration work, is by supplying username and password when logging in.

### Account ID

You can find your Account ID by going to https://www.nordnet.dk/oversigt/konto and

1. Use the number next to your account name in on the left'ish hand side of the screen under their logo
1. Use the the number at the end of the URL (e.g. `https://www.nordnet.dk/oversigt/konto/1` will be `Account ID` value `1`)

### Trading times

To avoid requesting data from the Nordnet API when the stock markets are closed (assuming mainly EU and US stock exchanges), you can set the `Start trading time` and `End trading time` to the hours where there would be changes in the underlying stocks.

Outside the configured trading hours, the integration will have a ~10% probablity (rather than 100%) of making a requst for new data from Nordnet API to refresh data, mainly to keep the login session alive and catch some after market changes.

The `Start trading time` and `End trading time` uses the [Time Zone configured in Home Assistant](https://www.home-assistant.io/blog/2015/05/09/utc-time-zone-awareness/)

### Query Nordnet API interval

How often the integration should refresh its data from the Nordnet API.

## State and attributes

A sensor for holding will be created with the `state` being the the total market value of the holding in `DKK`

 * `sensor.stock_price_for_alefarm_brewing_a_s_alefrm`
 * `sensor.stock_price_for_advanced_micro_devices_amd`
 * `sensor.stock_price_for_{name}_{ticker}`

There are a ton of attributes and they look like this (AMD stock example)

```yaml
state_class: measurement
device_class: monetary
icon: mdi:cash
friendly_name: Stock price for Advanced Micro Devices (AMD)
instrument:
  mifid2_category: 0
  price_type: monetary_amount
  tradables:
    - market_id: 19
      tick_size_id: 34830997
      display_order: 0
      lot_size: 1
      mic: XNAS
      price_unit: USD
      identifier: AMD
  instrument_id: 16120387
  asset_class: EQY
  instrument_type: ESH
  instrument_group_type: EQ
  currency: USD
  multiplier: 1
  pawn_percentage: 70
  margin_percentage: 120
  symbol: AMD
  isin_code: US0079031078
  name: Advanced Micro Devices

#################################################################################
# Generic
#################################################################################

account_id: *number                 # account id / index (1,2,3,4....)
account_number: *number             # account number
quantity: *number                   # number of stocks you own
unit_of_measurement: *string        # used for the "state" value which is ${account_currency}

#################################################################################
# Account values, in the ${account_currency} currency (e.g. DKK, SEK, NOK)
#################################################################################

account_currency: *string           # The currency of the trading account
account_acquisition_price: *float   # Average acquisition price per stock when you bought it
account_market_value: *float        # Total market value of your stocks - ${quantity} * ${account_acquisition_price}
account_roi: *float                 # Return Of Investment value
account_roi_percent: *float         # Return Of Investment percent

#################################################################################
# Position / stock values, in the ${position_currency} currency (e.g. USD, EUR)
#################################################################################

position_currency: *string          # The currency of the position (e.g. the stock, for APPL it would be USD)
position_acquisition_price: *float  # average acquisition price per stock when you bought it, in the native currency of the stock (e.g. USD)
position_market_price: *float       # current market price for 1 stock, in the native currency of the stock (e.g. USD)
position_market_value: *float       # total market value of your stocks, in the native currency of the stock (e.g. USD)
position_morning_price: *float      # price of the stock at opening of the market today, in the native currency of the stock (e.g. USD)
```

## Debugging

The intergration have pretty verbose debug logs, so if something is not working as expected, I would recommend moving to `debug` log level in `configuration.yaml`

```yaml
logger:
  default: warning
  logs:
    custom_components.nordnet: debug
```
