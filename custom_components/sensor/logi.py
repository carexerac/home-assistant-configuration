"""
This component provides HA sensor support for Logi Circle cameras.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.logi/
"""
from datetime import timedelta
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_ENTITY_NAMESPACE, CONF_MONITORED_CONDITIONS,
    STATE_UNKNOWN, ATTR_ATTRIBUTION)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.util.dt import as_local

DEPENDENCIES = ['logi']

DATA_LOGI = 'logi'
CONF_ATTRIBUTION = "Data provided by circle.logi.com"
DEFAULT_ENTITY_NAMESPACE = 'logi'

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

# Sensor types: Name, category, units, icon, kind
SENSOR_TYPES = {
    'battery_level': [
        'Battery', '%', 'battery-50'],

    'last_activity_time': [
        'Last Activity', None, 'history'],

    'speaker_volume': [
        'Volume', '%', 'volume-high'],

    'microphone_gain': [
        'Microphone Gain', '%', 'microphone'],

    'privacy_mode': [
        'Privacy Mode', None, 'eye'],

    'signal_strength_category': [
        'WiFi Signal Category', None, 'wifi'],

    'signal_strength_percentage': [
        'WiFi Signal Strength', '%', 'wifi'],

    'is_streaming': [
        'Streaming Mode', None, 'camera'],

    'temperature': [
        'Temperature', None, 'thermometer'],

    'humidity': [
        'Humidity', None, 'water-percent'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ENTITY_NAMESPACE, default=DEFAULT_ENTITY_NAMESPACE):
        cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up a sensor for a Logi Circle device."""
    logi = hass.data[DATA_LOGI]

    cameras = await logi.cameras
    sensors = []
    for sensor_type in config.get(CONF_MONITORED_CONDITIONS):
        for device in cameras:
            sensors.append(LogiSensor(hass, device, sensor_type))

    add_devices(sensors, True)
    return True


class LogiSensor(Entity):
    """A sensor implementation for a Logi Circle camera."""

    def __init__(self, hass, camera, sensor_type):
        """Initialize a sensor for Logi Circle camera."""
        super(LogiSensor, self).__init__()
        self._sensor_type = sensor_type
        self._camera = camera
        self._icon = 'mdi:{}'.format(SENSOR_TYPES.get(self._sensor_type)[2])
        self._name = "{0} {1}".format(
            self._camera.name, SENSOR_TYPES.get(self._sensor_type)[0])
        self._state = STATE_UNKNOWN
        self._tz = str(hass.config.time_zone)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
            'firmware': self._camera.firmware,
            'model': self._camera.model,
            'timezone': self._camera.timezone,
            'ip_address': self._camera.ip_address,
            'mac_address': self._camera.mac_address,
            'plan': self._camera.plan_name
        }

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if (self._sensor_type == 'battery_level' and
                self._state != STATE_UNKNOWN):
            return icon_for_battery_level(battery_level=int(self._state),
                                          charging=False)
        if (self._sensor_type == 'privacy_mode' and
                self._state != STATE_UNKNOWN):
            return 'mdi:eye-off' if self._state == 'on' else 'mdi:eye'
        if (self._sensor_type == 'is_streaming' and
                self._state != STATE_UNKNOWN):
            return 'mdi:camera' if self._state == 'on' else 'mdi:camera-off'
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return SENSOR_TYPES.get(self._sensor_type)[1]

    async def update(self):
        """Get the latest data and updates the state."""
        _LOGGER.debug("Pulling data from %s sensor", self._name)

        await self._camera.update()

        if self._sensor_type == 'last_activity_time':
            last_activity = await self._camera.last_activity
            if last_activity is not None:
                last_activity_time = as_local(last_activity.end_time_utc)
                self._state = '{0:0>2}:{1:0>2}'.format(
                    last_activity_time.hour, last_activity_time.minute)
        else:
            state = getattr(self._camera, self._sensor_type, STATE_UNKNOWN)
            if isinstance(state, bool):
                self._state = 'on' if state is True else 'off'
            else:
                self._state = state
