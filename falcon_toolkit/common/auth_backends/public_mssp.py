"""Falcon Toolkit: Public Cloud Flight Control (Multi-CID) Parent CID.

This authentication backend can take public cloud API keys (US-1, US-2, EU-1), and will ask the
user which child CID to authenticate against.
"""
import os

from typing import Dict, List

import keyring
import pick

from caracara import Client

from falcon_toolkit.common.auth import AuthBackend
from falcon_toolkit.common.auth_backends.utils import advanced_options_wizard
from falcon_toolkit.common.constants import KEYRING_SERVICE_NAME
from falcon_toolkit.common.utils import fancy_input


class PublicCloudFlightControlParentCIDBackend(AuthBackend):
    """Falcon Flight Control (Public Cloud) Authentication Backend.

    Authentication backend that uses a Client ID / Client Secret pair to access a Flight Control
    Parent CID. Once connected, a user can select a child CID to interface with.
    """

    name = "Falcon Flight Control MSSP Parent Falcon Tenant with multiple Customer IDs (CIDs)"
    simple_name = "PublicCloudFlightControlParentCID"
    description = (
        "A Falcon Flight Control (MSSP) Falcon tenant with multiple child Customer IDs (CIDs). "
        "These tenants are used in cases where a customer has multiple subsidiaries under central "
        "management, or where many customers have outsouced their Falcon management to a third "
        "party. This option is compatible with all of CrowdStrike's public cloud environments. "
        "For EU-1, US-1 and US-2, only a Client ID and Client Secret are required. For US "
        "GovCloud, set the Cloud Name to usgov1 within the additional options. "
        "NOTE: Each time you connect to a Flight Control CID you will be prompted on screen to "
        "choose a child CID to connect to. To skip this, set the environment variable "
        "FALCON_MSSP_CHILD_CID to the CID you want to connect to."
    )

    def __init__(self, config: Dict = None):
        """Retrieve the details needed to configure FalconPy from the user."""
        if config is None:
            config: Dict[str, object] = {}

        self.client_id: str = config.get("client_id")
        self.cloud_name: str = config.get("cloud_name", "auto")
        self.ssl_verify: bool = bool(config.get("ssl_verify", "False"))
        self.proxy: str = config.get("proxy")

        if config and self.client_id:
            # We handle the case where the authentication backend has failed, so we
            # have to get the client secret again. In this case, everything else is intact.
            self.client_secret: str = keyring.get_password(
                service_name=KEYRING_SERVICE_NAME,
                username=self.client_id,
            )
            if not self.client_secret:
                print("Client secret not available in the local secrets store. Please provide it.")
                self.client_secret = fancy_input("Client Secret: ")
        else:
            # If a config and Client ID are not available, we assume first time setup.
            self.client_id = fancy_input("Parent CID Client ID: ")
            self.client_secret = fancy_input("Parent CID Client Secret: ")

            advanced_options = advanced_options_wizard()
            self.cloud_name = advanced_options.cloud_name
            self.ssl_verify = advanced_options.ssl_verify
            self.proxy = advanced_options.proxy_config

        keyring.set_password(
            service_name=KEYRING_SERVICE_NAME,
            username=self.client_id,
            password=self.client_secret,
        )

    def dump_config(self) -> Dict[str, object]:
        """Return a dictionary with the data that must be written to the configuration file.

        Note that we do not return the Client Secret, as that is always stored away safely by
        keyring.
        """
        config: Dict[str, object] = {}
        config['client_id']: str = self.client_id
        config['cloud_name']: str = self.cloud_name
        config['ssl_verify']: bool = self.ssl_verify
        config['proxy']: Dict[str, str] = self.proxy

        return config

    def authenticate(self) -> Client:
        """Log the Toolkit into Falcon using the settings and keys configured at instance setup."""
        parent_client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            cloud_name=self.cloud_name,
            ssl_verify=self.ssl_verify,
            proxy=self.proxy,
        )
        child_cids = parent_client.flight_control.get_child_cids()
        chosen_cid_str = os.environ.get("FALCON_MSSP_CHILD_CID")
        if chosen_cid_str and chosen_cid_str.lower() in child_cids:
            chosen_cid = parent_client.flight_control.get_child_cid_data(
                cids=[chosen_cid_str]
            )[chosen_cid_str]
        else:
            child_cids_data = parent_client.flight_control.get_child_cid_data(cids=child_cids)

            options: List[pick.Option] = []
            for child_cid_str, child_cid_data in child_cids_data.items():
                child_cid_name = child_cid_data['name']
                option_text = f"{child_cid_str}: {child_cid_name}"
                option = pick.Option(label=option_text, value=child_cid_str)
                options.append(option)

            chosen_option, _ = pick.pick(options, "Please select a CID to connect to")
            chosen_cid_str = chosen_option.value
            chosen_cid = child_cids_data[chosen_cid_str]

        chosen_cid_name = chosen_cid['name']
        print(f"Connecting to {chosen_cid_name}")

        client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            cloud_name=self.cloud_name,
            member_cid=chosen_cid_str,
            ssl_verify=self.ssl_verify,
            proxy=self.proxy,
        )
        return client
