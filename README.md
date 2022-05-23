# Nordnet for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

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

The `Start trading time` and `End trading time` will be applied in the timezone you pick in the configuration menu to avoid confusing time zone conversion if your server is using UTC or another time zone than the one you live in.

### Query Nordnet API interval

How often the integration should refresh its data from the Nordnet API.


### Time between refreshing API login

How often should the intergration `login` from scratch again. Its mainly here to avoid login session timeouts and similar.

## State and attributes

A sensor for holding will be created with the `state` being the the total market value of the holding in `DKK`

 * `sensor.stock_price_for_alefarm_brewing_a_s_alefrm`
 * `sensor.stock_price_for_advanced_micro_devices_amd`
 * `sensor.stock_price_for_{name}_{ticker}`

There are a ton of attributes and they look like this (AMD stock example)

```yaml
state_class: measurement
accno: *number
accid: *number
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
market_value_acc_dkk: *float     # total market value of your stocks (DKK) - ${quantity} * ${acq_price_acc_dkk}
acq_price_acc_dkk: *float        # average acquisition price per stock when you bought it (DKK)
acq_price_usd: *float            # average acquisition price per stock when you bought it, in the native currency of the stock (e.g. USD)
acq_price_native: *float         # average acquisition price per stock when you bought it, in the native currency of the stock (e.g. USD)
market_value_usd: *float         # total market value of your stocks, in the native currency of the stock (e.g. USD)
market_value_native: *float      # total market value of your stocks, in the native currency of the stock (e.g. USD)
morning_price_usd: *float        # price of the stock at opening of the market today, in the native currency of the stock (e.g. USD)
morning_price_native: *float     # price of the stock at opening of the market today, in the native currency of the stock (e.g. USD)
main_market_price_usd: *float    # current market price for 1 stock, in the native currency of the stock (e.g. USD)
main_market_price_native: *float # current market price for 1 stock, in the native currency of the stock (e.g. USD)
quantity: *number                # number of stocks you own
roi_dkk: *float                  # return of investment in DKK
roi_percent: *float              # return of investment in %
unit_of_measurement: DKK         # used for the "state" value which is DKK
device_class: monetary           # used for the "state" value which is DKK
icon: mdi:cash                   # gotta love the icons!
friendly_name: Stock price for Advanced Micro Devices (AMD)
```

## Debugging

The intergration have pretty verbose debug logs, so if something is not working as expected, I would recommend moving to `debug` log level in `configuration.yaml`

```yaml
logger:
  default: warning
  logs:
    custom_components.nordnet: debug
```
