"""Falcon Toolkit: Public Cloud Flight Control (Multi-CID) Parent CID.

This authentication backend can take public cloud API keys (US-1, US-2, EU-1), and will ask the
user which child CID to authenticate against.
"""

from typing import Dict, Optional

import click
import keyring

from caracara import Client

from falcon_toolkit.common.auth import AuthBackend
from falcon_toolkit.common.auth_backends.utils import advanced_options_wizard
from falcon_toolkit.common.constants import KEYRING_SERVICE_NAME
from falcon_toolkit.common.utils import fancy_input, choose_cid


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
        "This option should be used only when you are connecting to a Parent CID; if you only have "
        "keys for a child CID, use the Single CID authentication backend instead. "
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

        if not config or not self.client_id:
            # If a config and Client ID are not available, we assume first time setup.
            self.client_id = fancy_input("Parent CID Client ID: ")
            self.client_secret = fancy_input("Parent CID Client Secret: ")

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
        config["client_id"] = self.client_id
        config["cloud_name"] = self.cloud_name
        config["ssl_verify"] = self.ssl_verify
        config["proxy"] = self.proxy

        return config

    def authenticate(self, ctx: click.Context) -> Client:
        """Log the Toolkit into Falcon using the settings and keys configured at instance setup."""
        chosen_cid_str = ctx.obj["cid"]

        parent_client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            cloud_name=self.cloud_name,
            ssl_verify=self.ssl_verify,
            proxy=self.proxy,
        )
        child_cids = parent_client.flight_control.get_child_cids()

        if chosen_cid_str and chosen_cid_str in child_cids:
            click.echo(
                click.style("Valid member CID ", fg="blue")
                + click.style(chosen_cid_str, fg="blue", bold=True)
                + click.style(" provided. Skipping CID selection.", fg="blue")
            )
        elif chosen_cid_str:
            click.echo(click.style("An invalid CID was provided at the command line.", fg="red"))
            click.echo("Please search for an alternative CID:")
            # Blank out a bad value
            chosen_cid_str = None

        if not chosen_cid_str:
            if chosen_cid_str and chosen_cid_str.lower() in child_cids:
                chosen_cid = parent_client.flight_control.get_child_cid_data(
                    cids=[chosen_cid_str],
                )[chosen_cid_str]
            else:
                child_cids_data = parent_client.flight_control.get_child_cid_data(cids=child_cids)
                if not child_cids_data:
                    raise RuntimeError(
                        "No child CIDs accessible. Please check your API credentials."
                    )

                chosen_cid_str = choose_cid(
                    cids=child_cids_data,
                    prompt_text="MSSP Child CID Search",
                )
                chosen_cid = child_cids_data[chosen_cid_str]

            chosen_cid_name = chosen_cid["name"]
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
