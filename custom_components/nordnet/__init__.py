import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORM
from .coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    See https://developers.home-assistant.io/docs/creating_component_index
    """

    _LOGGER.debug("async_setup called")

    hass.data[DOMAIN] = {}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Setting up configuration for each entry configured in the HA UI
    See: https://developers.home-assistant.io/docs/config_entries_index?_highlight=async_setup_entry#setting-up-an-entry
    """

    _LOGGER.debug(f"async_setup_entry called for entry '{entry.title}' (__init__.py)")

    # Create coordinator for the entry, responsible for fetching data from Nordnet
    # and creating entities for each listing in the account
    hass.data[DOMAIN][entry.entry_id] = Coordinator(hass, Coordinator.map_config(entry.options))

    # When an entry is updated via HA UI we will propagate the configuration
    # changes to the Coordinator
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # forward the entry to the platform
    # See: https://developers.home-assistant.io/docs/config_entries_index/#for-platforms
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """
    Called when an entry is updated via the HA UI - the listneer is bound in "async_setup_entry"
    e.g. you change your username or password for a Nordnet integration
    """

    _LOGGER.info(f"Updating entry configuration for entry '{entry.title}'")

    hass.data[DOMAIN][entry.entry_id].update_config(entry.options)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Called when an entity is disabled or deleted via the HA UI
    See: https://developers.home-assistant.io/docs/config_entries_index?_highlight=async_setup_entry#unloading-entries
    """

    _LOGGER.info(f"async_unload_entry called for entry '{entry.title}'")

    unload_ok = all(
        await asyncio.gather(
            hass.config_entries.async_forward_entry_unload(entry, "sensor"),
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """
    Migrate between configuration versions

    See https://developers.home-assistant.io/docs/config_entries_config_flow_handler#config-entry-migration
    """
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.options}

        new["trading_start_time"] = new["trading_start_hour"]
        new["trading_stop_time"] = new["trading_stop_hour"]

        del new["trading_start_hour"]
        del new["trading_stop_hour"]

        config_entry.version = 2

        hass.config_entries.async_update_entry(config_entry, options=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
