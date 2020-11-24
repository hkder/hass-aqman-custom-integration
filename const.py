"""Constants for the Aqman101 integration."""

# Integration Domain
DOMAIN = "aqman"

# Hass data keys
DATA_AQMAN_CLIENT = "aqman_client"

# Attributes
ATTR_IDENTIFIERS = "identifiers"
ATTR_MANUFACTURER = "manufacturer"
ATTR_MODEL = "model"
ATTR_ON = "on"
ATTR_SOFTWARE_VERSION = "sw_version"

# UNITS OF MEASUREMENT
RADON_BECQUEREL_PER_CUBIC_METER = "Bq/m³"

# Device Class
DEVICE_CLASS_RADON = "radon"
DEVICE_CLASS_CO2 = "co2"
DEVICE_CLASS_PM10 = "pm10"
DEVICE_CLASS_PM2D5 = "pm2d5"
DEVICE_CLASS_PM1 = "pm1"
DEVICE_CLASS_TVOC = "tvoc"