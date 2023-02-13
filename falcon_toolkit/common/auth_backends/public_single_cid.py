"""Falcon Toolkit: Public Cloud Single CID.

This authentication backend can take public cloud API keys (US-1, US-2, EU-1), and will return
an OAuth2 object suitable for authenticating with FalconPy.
"""
from typing import Dict, Optional

import keyring

from caracara import Client

from falcon_toolkit.common.auth import AuthBackend
from falcon_toolkit.common.auth_backends.utils import advanced_options_wizard
from falcon_toolkit.common.constants import KEYRING_SERVICE_NAME
from falcon_toolkit.common.utils import fancy_input


class PublicCloudSingleCIDBackend(AuthBackend):
    """Authentication backend that uses a Client ID / Client Secret pair to access public clouds."""

    name = "[Default] Standard Falcon Tenant with One Customer ID (CID)"
    simple_name = "PublicCloudSingleCID"
    description = (
        "A standard Falcon tenant with just one Customer ID (CID). This is the most common type of "
        "authentication backend, and should be considered the default. You will need to provide a "
        "Client ID and Client Secret pair. This option is compatible with all of CrowdStrike's "
        "public cloud environments. For EU-1, US-1 and US-2, only a Client ID and Client Secret "
        "are required. For US GovCloud, set the Cloud Name to usgov1 within the additional options."
    )

    def __init__(self, config: Dict = None):
        """Retrieve the details needed to configure FalconPy from the user."""
        if config is None:
            config: Dict[str, object] = {}

        self.client_id: str = config.get("client_id")
        self.cloud_name: str = config.get("cloud_name", "auto")
        self.ssl_verify: bool = bool(config.get("ssl_verify", "False"))
        self.proxy: Dict[str, str] = config.get("proxy")

        if not config or not self.client_id:
            # If a config and Client ID are not available, we assume first time setup.
            self.client_id = fancy_input("Client ID: ")
            self.client_secret = fancy_input("Client Secret: ")

            advanced_options = advanced_options_wizard()
            self.cloud_name = advanced_options.cloud_name
            self.ssl_verify = advanced_options.ssl_verify
            self.proxy = advanced_options.proxy_config

    @property
    def client_secret(self) -> str:
        """Loads the client secret dynamically from the system secret store.

        This has been moved to a property to partially address GitHub Issue #25.
        """
        _client_secret: Optional[str] = keyring.get_password(
            service_name=KEYRING_SERVICE_NAME,
            username=self.client_id,
        )
        if not _client_secret:
            print("Client secret not available in the local secrets store. Please provide it.")
            _client_secret = fancy_input("Client Secret: ")
            self.client_secret = _client_secret

        return _client_secret

    @client_secret.setter
    def client_secret(self, _client_secret: str):
        """Store the client secret in the system secrets store."""
        keyring.set_password(
            service_name=KEYRING_SERVICE_NAME,
            username=self.client_id,
            password=_client_secret,
        )

    def dump_config(self) -> Dict[str, object]:
        """Return a dictionary with the data that must be written to the configuration file.

        Note that we do not return the Client Secret, as that is always stored away safely by
        keyring.
        """
        config: Dict[str, object] = {}
        config['client_id'] = self.client_id
        config['cloud_name'] = self.cloud_name
        config['ssl_verify'] = self.ssl_verify
        config['proxy'] = self.proxy

        return config

    def authenticate(self) -> Client:
        """Log the Toolkit into Falcon using the settings and keys configured at instance setup."""
        client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            cloud_name=self.cloud_name,
            ssl_verify=self.ssl_verify,
            proxy=self.proxy,
        )
        return client
