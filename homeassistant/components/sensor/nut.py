"""
Provides a sensor to track various status aspects of a UPS.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.nut/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.components import nut
from homeassistant.const import (TEMP_CELSIUS, CONF_RESOURCES)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [nut.DOMAIN]

SENSOR_PREFIX = 'UPS '
SENSOR_TYPES = {
    'battery_charge': ['Battery', '%', 'mdi:battery'],
    'battery_charge_low': ['Battery Critical', '%', 'mdi:battery'],
    'battery_charge_warning': ['Battery Warning', '%', 'mdi:battery'],
    'battery_runtime': ['Runtime', 'min', 'mdi:calendar-clock'],
    'battery_runtime_low': ['Runtime Critical', 'min', 'mdi:calendar-clock'],
    'battery_temperature': ['Battery Temperature', TEMP_CELSIUS, 'mdi:thermometer'],
    'battery_voltage': ['Battery Voltage', 'V', 'mdi:flash'],
    'battery_voltage_nominal': ['Battery Nominal Voltage', 'V', 'mdi:flash'],
    'input_voltage': ['Input Voltage', 'V', 'mdi:flash'],
    'output_voltage': ['Output Voltage', 'V', 'mdi:flash'],
    'output_voltage_nominal': ['Nominal Output Voltage', 'V', 'mdi:flash'],
    'ups_load': ['Load', '%', 'mdi:gauge']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the NUT sensors."""
    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [
                sensor_type.title(), '', 'mdi:information-outline']

        if sensor_type.lower() not in nut.DATA.status:
            _LOGGER.warning(
                'Sensor type: "%s" does not appear in the NUT status '
                'output', sensor_type)

        entities.append(NUTSensor(nut.DATA, sensor_type))

    add_entities(entities)

class NUTSensor(Entity):
    """Representation of a sensor entity for NUT status values."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self._data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + SENSOR_TYPES[sensor_type][0]
        self._unit = SENSOR_TYPES[sensor_type][1]
        self.update()

    @property
    def name(self):
        """Return the name of the UPS sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][2]

    @property
    def state(self):
        """Return true if the UPS is online, else False."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    def update(self):
        """Get the latest status and use it to update our sensor state."""
        if self.type.lower() not in self._data.status:
            self._state = None
        else:
            self._state = self._data.status[self.type.lower()]
