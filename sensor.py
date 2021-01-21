"""Support for Radon FtLabs Aqman101"""
import logging
from datetime import datetime, timedelta
import time
from typing import Callable, List
import asyncio

from aqman import AqmanDevice, Device, AqmanError
import voluptuous as vol

from homeassistant.helpers import device_registry as dr
from homeassistant.components.air_quality import PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.const import ATTR_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
)

from .const import (
    DOMAIN,
    DATA_AQMAN_CLIENT,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_ON,
    ATTR_SOFTWARE_VERSION,
    RADON_BECQUEREL_PER_CUBIC_METER,
    DEVICE_CLASS_RADON,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_PM10,
    DEVICE_CLASS_PM2D5,
    DEVICE_CLASS_PM1,
    DEVICE_CLASS_TVOC,
)

DEFAULT_NAME = "Radon FtLabs Aqman101"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=2)

SENSOR_TYPES = {
    "temperature": [TEMP_CELSIUS, "temperature", DEVICE_CLASS_TEMPERATURE],
    "humidity": [PERCENTAGE, "humidity", DEVICE_CLASS_HUMIDITY],
    "radon": [RADON_BECQUEREL_PER_CUBIC_METER, "radon", DEVICE_CLASS_RADON],
    "carbon_dioxide": [CONCENTRATION_PARTS_PER_MILLION, "co2", DEVICE_CLASS_CO2],
    "particulate_matter_10": [
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "pm10",
        DEVICE_CLASS_PM10,
    ],
    "particulate_matter_2_5": [
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "pm2d5",
        DEVICE_CLASS_PM2D5,
    ],
    "particulate_matter_1": [
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "pm1",
        DEVICE_CLASS_PM1,
    ],
    "total_volatile_organic_compounds": [
        CONCENTRATION_PARTS_PER_BILLION,
        "tvoc",
        DEVICE_CLASS_TVOC,
    ],
}

SENSORS = [
    "temperature",
    "humidity",
    "radon",
    "carbon_dioxide",
    "particulate_matter_10",
    "particulate_matter_2_5",
    "particulate_matter_1",
    "total_volatile_organic_compounds",
]


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Aqman101 from config entry"""

    entities = []
    devices = entry.data[CONF_DEVICES]

    for device in devices:
        aqman_instance: AqmanDevice = AqmanDevice(
            deviceid=device,
        )
        aqman_instance_state: Device = await aqman_instance.state()
        hass.data[DOMAIN].setdefault(device, aqman_instance_state)
        for sensor in SENSORS:
            entities.append(AqmanBaseSensor(device, devices, sensor, hass))

        await aqman_instance.close()

    # _LOGGER.warning("%s", hass.data[DOMAIN])

    async_add_entities(entities)


class AqmanBaseSensor(Entity):
    """Base class for an Aqman Sensor Entity"""

    def __init__(
        self,
        deviceid: str = None,
        devices: List[str] = None,
        sensor_type: str = None,
        hass: HomeAssistantType = None,
    ):
        """Initialize a Aqman Base Sensor Instance"""
        self._deviceid = deviceid
        self._devices = devices
        self._sensor_type = sensor_type
        self._aqman_type = SENSOR_TYPES.get(self._sensor_type)[1]

        self._aqman_instance_state = hass.data[DOMAIN][deviceid]
        self._serial_number = self._aqman_instance_state.serial_number
        self._dsm101_serial_number = self._aqman_instance_state.dsm101_serial_number
        self._fw_version = self._aqman_instance_state.firmware_version
        self._date_time = self._aqman_instance_state.date_time
        self._is_available = True
        self._state = getattr(self._aqman_instance_state, self._aqman_type)
        self._device_state_attributes = {
            "last_update": self._date_time,
            "value": self._state,
        }
        self._hass = hass

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._serial_number}.{self._aqman_type}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._serial_number}.{self._aqman_type}"

    @property
    def device_id(self) -> str:
        """Return the device id"""
        return self._deviceid

    @property
    def device_info(self):
        """Return the device info of the Aqman101 device."""
        device_info = {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._serial_number)},
            "identifiers": {(DOMAIN, self._serial_number)},
            "manufacturer": "Radon FTLabs",
            "model": "aqman101",
            "name": f"{self._serial_number}",
            "sw_version": f"{self._fw_version}",
            # "via_device":
        }
        return device_info

    @property
    def available(self):
        return self._is_available

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return (
            SENSOR_TYPES.get(self._sensor_type)[2]
            if self._sensor_type in SENSOR_TYPES
            else None
        )

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        try:
            return SENSOR_TYPES.get(self._sensor_type)[0]
        except TypeError:
            return None

    @property
    def last_update(self):
        """Returns the last update time."""
        return self._date_time

    @property
    def device_state_attributes(self):
        """Return the state attributes"""
        return self._device_state_attributes

    async def update_devices(self):
        first_device = self._devices[0]

        if self._deviceid == first_device and self._aqman_type == "temperature":
            try:
                for device in self._devices:
                    aqman_instance: AqmanDevice = AqmanDevice(
                        deviceid=device,
                    )
                    state: Device = await aqman_instance.state()
                    self._hass.data[DOMAIN][device] = state

                    await aqman_instance.close()
            except AqmanError:
                _LOGGER.error("An error occurred while updating Aqman101")
                await aqman_instance.close()
                return
        else:
            await asyncio.sleep(1)

        return self._hass.data[DOMAIN][self._deviceid]

    async def async_update(self):
        """Update Aqman Sensor Entity"""
        state = await self.update_devices()
        try:
            # _LOGGER.warning("Updated %s-%s === %s", self._deviceid, self._aqman_type, state)
            self._date_time = state.date_time
            self._state = getattr(state, self._aqman_type)
            self._device_state_attributes["last_update"] = self._date_time
            self._device_state_attributes["value"] = self._state
        except AttributeError:
            # Meaning that state is None
            pass
