"""Config flow for Aqman101."""
import logging
from typing import Any, Dict, Optional

from aqman import AqmanUser, AqmanDevice, AqmanError, UserInfo, Device
import voluptuous as vol

from homeassistant.helpers import config_entry_flow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigFlow
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AqmanFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Aqman 101 config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize"""
        self.user = None

    async def async_step_user(
        self, user_input: Optional[ConfigType] = None
    ) -> Dict[str, Any]:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self._show_setup_form()

        try:
            user: UserInfo = await self._get_aqman_user(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
        except AqmanError:
            return self._show_setup_form({"base": "cannot_connect"})

        # Check if already configured
        await self.async_set_unique_id(user_input[CONF_USERNAME])
        self._abort_if_unique_id_configured()

        if user.device_cnt > 0:
            self.user = user
            return await self.async_step_select()

        return self._show_setup_form({"base": "no devices to connect"})

    async def async_step_select(self, user_input=None):
        """Handle multiple devices found."""
        if user_input is None or "select_devices" not in user_input:
            return self._show_step_select()

        _LOGGER.warning(user_input["select_devices"])

        return self.async_create_entry(
            title=self.user.username.upper(),
            data={
                CONF_USERNAME: self.user.username,
                CONF_PASSWORD: self.user.password,
                CONF_DEVICES: user_input["select_devices"],
            },
        )

    def _show_step_select(self, errors={}):
        select_schema = vol.Schema(
            {
                vol.Required("select_devices"): cv.multi_select(
                    {device: device for idx, device in enumerate(self.user.devices)}
                )
            }
        )

        return self.async_show_form(
            step_id="select", data_schema=select_schema, errors=errors
        )

    def _show_setup_form(self, errors: Optional[Dict] = None) -> Dict[str, Any]:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors or {},
        )

    async def _get_aqman_user(self, username: str, password: str) -> UserInfo:
        """Get device state from an Aqman 101 device"""
        aqman_user: AqmanUser = AqmanUser(id=username, password=password)
        info = await aqman_user.devices_info()
        await aqman_user.close()
        return info
