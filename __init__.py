"""The Aqman101 integration."""
from aqman import AqmanDevice, Device, AqmanConnectionError

import logging
import asyncio

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity import Entity

from .const import DATA_AQMAN_CLIENT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Aqman101 component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aqman101 from a config entry."""

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    devices = entry.data[CONF_DEVICES]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, entry.data)

    device_registry = await dr.async_get_registry(hass)

    for device in entry.data[CONF_DEVICES]:

        # aqman_device = AqmanDevice(
        #     id=entry.data[CONF_USERNAME],
        #     password=entry.data[CONF_PASSWORD],
        #     deviceid=device,
        # )

        # try:
        #     device: Device = await aqman_device.state()
        # except AqmanConnectionError as e:
        #     raise ConfigEntryNotReady from e

        # await aqman_device.close()

        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, device)},
            identifiers={(DOMAIN, device)},
            manufacturer="Radon FTLabs",
            name=device,
            model="aqman101",
            # sw_version=device.firmware_version,
        )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):

    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    # Cleanup entry
    del hass.data[DOMAIN][entry.entry_id]
    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    return True
