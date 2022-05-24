"""Constants for the Nordnet integration."""

DOMAIN = "nordnet"
PLATFORM = "sensor"

########################
# config flow
########################

DEFAULT_ACCOUNT_ID = 1

# Covers most of the European and American markets
DEFAULT_TRADING_START_TIME = "09:00:00"
DEFAULT_TRADING_STOP_TIME = "23:00:00"

DEFAULT_UPDATE_INTERVAL = {
    "hours": 0,
    "minutes": 0,
    "seconds": 30
},

DEFAULT_SESSION_LIFETIME = {
    "hours": 24,
    "minutes": 0,
    "seconds": 0
}

########################
# Coordinator
########################

"""
Headers sent in all requests to Nordnet APIs
"""
DEFAULT_HEADERS = {
    'client-id': 'NEXT',
    'sub-client-id': 'NEXT',
}

"""
The number of seconds requesting data from Nordnet API can take
before the request is canceled
"""
UPDATE_TIMEOUT = 10  # seconds
