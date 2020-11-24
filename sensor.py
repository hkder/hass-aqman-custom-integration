"""Support for Radon FtLabs Aqman101"""
import logging
from datetime import datetime, timedelta
from typing import Callable, List

from aqman import AqmanDevice, Device, AqmanError
import voluptuous as vol

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

SCAN_INTERVAL = timedelta(minutes=10)

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

    # coordinator = DataUpdateCoordinator(
    #     hass=hass,
    #     logger=_LOGGER,
    #     name="sensor",
    #     update_interval=timedelta(seconds=10),
    #     update_method=async_update_data,
    # )

    for device in devices:
        aqman_instance: AqmanDevice = AqmanDevice(
            id=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            deviceid=device,
        )
        aqman_instance_state: Device = await aqman_instance.state()
        for sensor in SENSORS:
            entities.append(
                AqmanBaseSensor(sensor, aqman_instance, aqman_instance_state)
            )

    async_add_entities(entities)


class AqmanBaseSensor(Entity):
    """Base class for an Aqman Sensor Entity"""

    def __init__(
        self,
        sensor_type: str = None,
        aqman_instance: AqmanDevice = None,
        aqman_instance_state: Device = None,
    ):
        """Initialize a Aqman Base Sensor Instance"""
        self._sensor_type = sensor_type
        self._aqman_instance = aqman_instance
        self._serial_number = aqman_instance_state.serial_number
        self._dsm101_serial_number = aqman_instance_state.dsm101_serial_number
        self._date_time = aqman_instance_state.date_time
        self._is_available = True
        self._aqman_type = SENSOR_TYPES.get(self._sensor_type)[1]
        self._state = getattr(aqman_instance_state, self._aqman_type)
        self._device_state_attributes = {"last_update": self._date_time}

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._serial_number}.{self._aqman_type}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._serial_number}.{self._aqman_type}"

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
    def should_poll(self):
        """Return the polling state. Polling is needed."""
        return True

    @property
    def device_state_attributes(self):
        """Return the state attributes"""
        return self._device_state_attributes

    async def async_update(self):
        """Update Aqman Sensor Entity"""
        try:
            state: Device = await self._aqman_instance.state()
            _LOGGER.debug("Got new state: %s", state)
        except AqmanError:
            if self._is_available:
                _LOGGER.error("An error occurred while updating Aqman101")
            self._is_available = False
            return

        self._date_time = state.date_time
        self._state = getattr(state, self._aqman_type)
        self._device_state_attributes["last_update"] = self._date_time
