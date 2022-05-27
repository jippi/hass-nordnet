"""
The coordinatator is repsonsible for talking to Nordnet API and signal entities
to update their state and attributes
"""

import logging
import random
from datetime import datetime, time, timedelta
from typing import TypedDict

import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt

from .const import DEFAULT_HEADERS, UPDATE_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class CoordinatorConfig(TypedDict):
    """
    Coordinator configuration from HA UI settings converted into their native Python types
    """
    username: str
    password: str
    account_id: int
    account_currency: str
    trading_start_time: time
    trading_stop_time: time
    session_lifetime: timedelta
    update_interval: timedelta


class Coordinator(DataUpdateCoordinator):
    """
    The coordinator is responsible for fetching data from the Nordnet API
    and make it available to the entities that gets created from each holding
    in tthe configured Nordnet account
    """

    def __init__(self, hass: HomeAssistant, config: CoordinatorConfig):
        _LOGGER.debug("Creating Nordnet holdings coordinator")

        super().__init__(hass, _LOGGER, name="nordnet", update_interval=config["update_interval"])

        self.config: CoordinatorConfig = config

        self._hass: HomeAssistant = hass
        self._holdings: dict = None
        self._session: aiohttp.ClientSession = None
        self._session_created_at: datetime = None

    def update_config(self, config: dict) -> None:
        """
        Update the internal config dict with new settings made in HA UI

        We also reset the session so any credentials changes made will
        take effect on next fetch from Nordnet API
        """

        # update internal configuration
        self.config = Coordinator.map_config(config)

        # force creation of a new HTTP session
        self._session = None

        # property in parent DataUpdateCoordinator
        self.update_interval = self.config["update_interval"]

    def account_currency(self)->str:
        return self.config['account_currency']

    def holdings(self) -> dict:
        """
        Return the full raw holdings response from Nordnet

        Used on startup to creator sensors for all holdings in the account
        """

        return self._holdings

    def holding_for_symbol(self, symbol) -> dict:
        """
        Find the position associated with a specific trading symbol.
        Used in sensor.py to check for new data
        """

        for position in self._holdings:
            if position['instrument']['symbol'] == symbol:
                return position

        return None

    async def get_account_details(self)->dict:
        session = await self._authenticated_session()
        response = await session.get(f"https://www.nordnet.dk/api/2/accounts/{self.config['account_id']}/info", headers=DEFAULT_HEADERS)
        response.raise_for_status()

        data = await response.json()
        return data[0]

    async def _handle_refresh_interval(self, _now: datetime) -> None:
        """
        Overriding parent func to prevent any calls to _async_update_data outside trading windows
        as it will be a lot more spammy in logs, and will advertly always "succeed" outside trading windows
        making error tracking pretty hard
        """

        if self._should_make_request() is False:
            self._debounced_refresh.async_cancel()
            self._schedule_refresh()

            return

        return await super()._handle_refresh_interval(_now)

    async def _async_update_data(self) -> None:
        """
        Called by Home Assistant every config['update_interval'] in sensor.py to refresh data
        """

        _LOGGER.debug("Refreshing data from Nordnet API")

        async with async_timeout.timeout(UPDATE_TIMEOUT):
            _LOGGER.debug("Getting HTTP session")
            session = await self._authenticated_session()

            _LOGGER.debug(f"Requesting stock positions from Nordnet API for account {self.config['account_id']}")
            response = await session.get(f"https://www.nordnet.dk/api/2/accounts/{self.config['account_id']}/positions", headers=DEFAULT_HEADERS)
            response.raise_for_status()

            self._holdings = await response.json()

            _LOGGER.debug("Successfully updated stock positions from Nordnet API")

    def _should_make_request(self) -> bool:
        """
        Check if we should make a Nordnet API request for Stock holdings
        If we're outside trading hours for example, there will be no changes to the underlying data
        so we might as well not hit their API at all to not abuse their service
        """

        # If we never requested data from Nordnet, like after a restart, always fetch it
        if self._holdings == None:
            _LOGGER.debug("No local holdings found, will query Nordnet API")
            return True

        # inside trading hours, go forth and request Nordnet
        if self._inside_trading_window():
            _LOGGER.debug(f"Within trade window, will query Nordnet API")
            return True

        # outside trading hours, we will update once in a while to keep things... fresh
        if self._outside_trading_window_probability():
            _LOGGER.debug(
                f"Not inside trading hours ({self.config['trading_start_time']} - {self.config['trading_stop_time']}), but will query Nordnet API anyway")
            return True

        # outside trading hours, no dice
        _LOGGER.debug(
            f"Not inside trading hours ({self.config['trading_start_time']} - {self.config['trading_stop_time']}), will not query Nordnet API")
        return False

    def _outside_trading_window_probability(self) -> bool:
        """
        Just a slight randomizer for doing fewer Nordnet API requests outside trading windows
        """

        return random.randint(0, 10) == 5

    async def _authenticated_session(self) -> aiohttp.ClientSession:
        """
        Returns a HTTP Session containing all required Cookies for a making authenticated
        api requests to the Nordnet API
        """
        _LOGGER.debug("Called _get_session")

        if self._has_valid_session():
            _LOGGER.debug(f"Returning existing HTTP session")
            return self._session

        _LOGGER.debug(f"[session] Creating new HTTP session")

        session = async_create_clientsession(self._hass)

        # Setting cookies prior to login by visiting login page
        _LOGGER.debug("[session] requesting website login page")
        async with session.get('https://www.nordnet.dk/logind') as response:
            _LOGGER.debug("[session] checking website login response")
            response.raise_for_status()

            # read the resposne but discard it
            await response.text()
            _LOGGER.debug("[session] website login OK")

        # Actual login
        _LOGGER.debug("[session] requesting API bastic auth login")
        async with session.post('https://www.nordnet.dk/api/2/authentication/basic/login',
                                data={'username': self.config["username"], 'password': self.config["password"]},
                                headers=DEFAULT_HEADERS) as response:
            _LOGGER.debug("[session] checking API basic auth login reaponse")
            response.raise_for_status()

            # read the response but discard it
            await response.text()
            _LOGGER.debug("[session] API bastic auth login OK")

        self._session = session
        self._session_created_at = dt.now()

        _LOGGER.debug("[session] Returning the new HTTP session")
        return self._session

    def _has_valid_session(self) -> bool:
        """
        Check if the HTTP session has expired and needs renewal
        """

        # if we don't have a session, force creation of a new one
        if self._session is None:
            return False

        # check the age of the session and compare with our session max age
        age = dt.now() - self._session_created_at
        return age < self.config["session_lifetime"]

    def _inside_trading_window(self) -> bool:
        """
        Check if we're within the trading window
        """

        now = dt.now()

        # trading doesn't happen on Saturday or Sunday, hardcoding this for now
        # since I'm not having any stocks outside EU and US trading hours
        day_of_week = now.strftime('%A')
        if day_of_week in ['Saturday', 'Sunday']:
            _LOGGER.debug(f"{day_of_week} is not a trading day, skipping...")
            return False

        # Trading is open between 09:00 and 23:00 in Europe/Copenhagen
        if not self.config["trading_start_time"] <= now.time() < self.config["trading_stop_time"]:
            return False

        return True

    @staticmethod
    def map_config(input: dict) -> CoordinatorConfig:
        """
        Convert the options dict into a CoordinatorConfig dict
        """

        config = dict(input)

        config["account_id"] = int(config["account_id"])

        config["trading_start_time"] = time.fromisoformat(config["trading_start_time"])
        config["trading_stop_time"] = time.fromisoformat(config["trading_stop_time"])

        config["update_interval"] = duration_to_timedelta(config["update_interval"])
        config["session_lifetime"] = timedelta(minutes=55) # sessions expire after 1h

        return config


def duration_to_timedelta(x: dict) -> timedelta:
    """
    Converts the HA 'duration' selector into a Python timedelta
    """
    return timedelta(hours=x["hours"], minutes=x["minutes"], seconds=x["seconds"])
