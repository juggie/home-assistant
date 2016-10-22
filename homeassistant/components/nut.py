"""
Support for status output of NUT.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/nut/
"""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import (CONF_HOST, CONF_PORT, CONF_UPS_NAME)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

REQUIREMENTS = ['nut2==2.1.0']

_LOGGER = logging.getLogger(__name__)

CONF_TYPE = 'type'

DATA = None
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 3493
DEFAULT_UPS_NAME = None
DOMAIN = 'nut'

KEY_STATUS = 'ups_status'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

VALUE_ONLINE = 'OL'

CONVERT_TIME = ['battery.runtime', 'battery.runtime.low']

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_UPS_NAME, default=DEFAULT_UPS_NAME): cv.string,        
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Use config values to set up a function enabling status retrieval."""
    global DATA
    conf = config[DOMAIN]
    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)
    ups = conf.get(CONF_UPS_NAME)

    DATA = NUTData(host, port, ups)

    # It doesn't really matter why we're not able to get the status, just that
    # we can't.
    # pylint: disable=broad-except
    try:
        DATA.update(no_throttle=True)
    except Exception:
        _LOGGER.exception("Failure while testing NUT status retrieval.")
        return False
    return True


class NUTData(object):
    """Stores the data retrieved from NUT.

    For each entity to use, acts as the single point responsible for fetching
    updates from the server.
    """

    def __init__(self, host, port, ups):
        """Initialize the data oject."""
        from nut2 import PyNUTClient
        self._status = None

        #If users don't set UPS name and only one UPS registered to nut, use that, else fail.
        if ups is not None:
            self._ups = ups
        else:
            upslist = PyNUTClient(host=host, port=port).list_ups()
            if len(upslist) == 1:
                self._ups = list(upslist.keys())[0]
            else:
                self._ups = None

        self._client = PyNUTClient(host=host, port=port)

    @property
    def status(self):
        """Get latest update if throttle allows. Return status."""
        self.update()
        return self._status

    def _get_status(self):
        """Get the status from NUT and parse it into a dict."""
        ret = {}
        upsvars = self._client.list_vars(self._ups)
        for k, v in upsvars.items():
            print(k)
            if k in CONVERT_TIME:
                ret[k.replace('.', '_')] = round(int(v)/60.0, 1)
            else:
                ret[k.replace('.', '_')] = v
        return ret

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        """Fetch the latest status from NUT."""
        self._status = self._get_status()
        print(self._status)
