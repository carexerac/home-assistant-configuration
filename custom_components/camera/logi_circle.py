"""
Support for Logi Circle camera.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.logi_circle/
"""

import logging
import requests
import xml.etree.ElementTree as ET
import voluptuous as vol
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
from homeassistant.components.camera import Camera, PLATFORM_SCHEMA
from homeassistant.const import (CONF_EMAIL, CONF_PASSWORD)
from homeassistant.util import Throttle

CONF_BASE_URI = 'https://video.logi.com'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30) # the interval on the Logi Web Interface is 30s, no idea what the backend is

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up all the Logi Circle cameras connected to the provided account."""
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)

    session = requests.Session() # we need to keep the same session between requests

    try:
        auth_url = '{}/api/accounts/authorization'.format(CONF_BASE_URI)
        _LOGGER.debug('>> POST %s', auth_url)
        auth_request = session.post(
            url=auth_url,
            json={
                'email': email,
                'password': password
            },
            headers={
                'Accept': 'application/json'
            }
        )
        _LOGGER.debug('<< POST %s\n%s %s %s\n%s', auth_request.url, auth_request.status_code, auth_request.reason, auth_request.headers, auth_request.content)

        accessories_url = '{}/api/accessories'.format(CONF_BASE_URI)
        _LOGGER.debug('>> GET %s', accessories_url)
        accessories_request = session.get(
            url=accessories_url,
            headers={
                'Accept': 'application/json',
            }
        )
        _LOGGER.debug('<< GET %s\n%s %s %s\n%s', accessories_request.url, accessories_request.status_code, accessories_request.reason, accessories_request.headers, accessories_request.content)
        accessories = accessories_request.json()

        add_devices(LogiCircleCamera(accessory, session) for accessory in accessories)
        return True
    except (
        requests.exceptions.Timeout,
        requests.exceptions.TooManyRedirects,
        requests.exceptions.RequestException,
        requests.exceptions.HTTPError
    ) as e:
        return False

class LogiCircleCamera(Camera):
    """Representation of a Logi Circle camera."""

    def __init__(self, data, session):
        """Initialize a Logi Circle camera."""
        super().__init__()

        self._accessory_id = data['accessoryId']
        self._node_id = data['nodeId']
        self._name = data['name']
        self._created = data['created']
        self._session = session
        self._image = None
        self.update()

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def created(self):
        """Return the creation date of this camera."""
        return self._created

    def update(self):
        """Fetch new state data for this camera.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.update_image()

    def camera_image(self):
        self.update_image()
        return self._image

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update_image(self):
        """Fetch and return newest image content.

        Keep in mind that as of 2018-01-15 it is only updated every 30s on the Logi Circle API."""
        image_url = "https://{}/api/accessories/{}/image".format(self._node_id, self._accessory_id)
        _LOGGER.debug('>> GET %s', image_url)
        image_request = self._session.get(image_url)
        _LOGGER.debug('<< GET %s\n%s %s', image_request.url, image_request.status_code, image_request.reason)
        self._image = image_request.content

    def get_video(self, seconds=30):
        """Fetch MPEGDash segments and concat them as a MP4 video file."""
        mpd_url = "https://{}/api/accessories/{}/mpd".format(self._node_id, self._accessory_id)
        _LOGGER.debug('>> GET %s', mpd_url)
        mpd_request = s.get(mpd_url)
        _LOGGER.debug('<< GET %s\n%s %s %s\n%s', mpd_request.url, mpd_request.status_code, mpd_request.reason, mpd_request.headers, mpd_request.content)

        xml_root = ET.fromstring(mpd_request.content)

        base_url = xml_root.find('{urn:mpeg:dash:schema:mpd:2011}BaseURL').text
        segment_template = xml_root.find('{urn:mpeg:dash:schema:mpd:2011}SegmentTemplate')
        init_url = "{}{}".format(base_url, segment_template.get('initialization'))
        _LOGGER.debug('>> GET %s', init_url)
        init_request = s.get(init_url)
        _LOGGER.debug('<< GET %s\n%s %s', init_request.url, init_request.status_code, init_request.reason)

        video_content = init_request.content
        for i in range(segment_template.get('startNumber'), seconds * segment_template.get('timescale') / segment_template.get('duration')):
            media_url = "{}{}".format(base_url, segment_template.get('media').replace('$Number$', str(i)))
            _LOGGER.debug('>> GET %s', media_url)
            media_request = s.get(media_url)
            _LOGGER.debug('<< GET %s\n%s %s', media_request.url, media_request.status_code, media_request.reason)
            video_content += media_request.content

        # with open("video.mp4", 'wb') as file:
        #     file.write(video_content)
        return video_content