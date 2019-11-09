"""
Support for interface with a Serverless Nabaztag.

For more details about this platform, please refer to the documentation at
the [README.md](./README.md)
"""
import logging
import voluptuous as vol
import requests

from homeassistant.helpers.entity import Entity
from homeassistant.components.media_player import (
  MediaPlayerDevice,
  PLATFORM_SCHEMA
)
from homeassistant.components.media_player.const import (
  SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_PLAY,
  SUPPORT_PLAY_MEDIA, SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET,
  SUPPORT_SELECT_SOURCE, SUPPORT_STOP, MEDIA_TYPE_MUSIC)
from homeassistant.const import (CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON)
import homeassistant.helpers.config_validation as cv

__version__ = '1.0.0'

REQUIREMENTS = ['']

_LOGGER = logging.getLogger(__name__)

SUPPORT_NABAZTAG = SUPPORT_PLAY_MEDIA

DEFAULT_NAME = 'Nabaztag'
DEVICE_CLASS = 'speaker'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Nabaztag platform."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    if host is None:
        _LOGGER.error("No IP address found in configuration file")
        return

    add_devices([Nabaztag(host, name)])


class Nabaztag(MediaPlayerDevice):
    """Representation of a Nabaztag."""

    def __init__(self, host, name):
        """Initialize the Nabaztag device."""
        _LOGGER.info("Setting up fucking Nabaztag")

        self._host = host
        self._name = name
        self._unique_id = '{}-{}'.format(host, name)

        _LOGGER.debug("Set up Nabaztag with IP: %s", host)

        self.update()

    def update(self):
        """Update TV info."""
        self._state = STATE_ON

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the device."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def device_class(self):
        """Return the device class of the media player."""
        return DEVICE_CLASS

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_NABAZTAG

    @property
    def media_content_type(self):
        """Content type of current playing media.
        Used for program information below the channel in the state card.
        """
        return MEDIA_TYPE_MUSIC

    def play_media(self, media_type, media_id, **kwargs):
        """Play media."""
        _LOGGER.debug("Play media: %s (%s)", media_id, media_type)

        play_request = requests.get(url = 'http://{0}/play'.format(self._host), params = { 'u': media_id })
