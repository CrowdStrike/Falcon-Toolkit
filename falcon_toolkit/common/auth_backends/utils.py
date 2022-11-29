"""Falcon Toolkit: Authentication Backends.

This file contains functions to be shared between all the authentication backends we
provide out of the box, as well as any that developers may write in the future. It is
designed to avoid excessive code-reuse between similar implementations of auth backend.
This file provides:
- A list of all public CrowdStrike clouds
- A cloud selection function to allow a user to choose a cloud via pick
- Advanced options configuration for overriding cloud, TLS validation, etc.
"""
from typing import (
    Dict,
    List,
    NamedTuple,
)

import pick

from falcon_toolkit.common.utils import fancy_input


CLOUDS = {
    "auto": "Automatic cloud selection (supports US-1, US-2 and EU-1)",
    "us-1": "US-1: Falcon US-1 Falcon cloud (api.crowdstrike.com)",
    "us-2": "US-2: Falcon US-2 Falcon cloud (api.us-2.crowdstrike.com)",
    "eu-1": "EU-1: Falcon EU (Germany) cloud (api.eu-1.crowdstrike.com)",
    "us-gov-1": "US-GOV-1: Falcon in GovCloud (api.laggar.gcw.crowdstrike.com)",
}


def cloud_choice() -> str:
    """Configure a selection of clouds and allow the user to choose one via pick."""
    cloud_choices: List[pick.Option] = []
    for cloud_id, cloud_description in CLOUDS.items():
        cloud_choices.append(pick.Option(cloud_description, cloud_id))

    chosen_option, _ = pick.pick(cloud_choices, title="Please choose a Falcon cloud")
    chosen_falcon_cloud: str = chosen_option.value

    return chosen_falcon_cloud


class AdvancedOptionsType(NamedTuple):
    """Named Tuple that contains the results of the Advanced Options Wizard."""

    cloud_name: str
    ssl_verify: bool
    proxy_config: Dict[str, str]


def advanced_options_wizard() -> AdvancedOptionsType:
    """Define advanced connection options and return an AdvancedOptionsType."""
    advanced_options_input = fancy_input("Do you want to configure more options? [y/n]: ")
    if advanced_options_input not in ('y', 'Y'):
        return AdvancedOptionsType('auto', True, None)

    cloud_name = cloud_choice()

    tls_verify_options: List[pick.Option] = [
        pick.Option("Verify SSL/TLS certificates (recommended!)", value=True),
        pick.Option("Do not verify SSL/TLS certificates (not recommended)", False),
    ]
    chosen_ssl_verify, _ = pick.pick(tls_verify_options, title="Verify SSL/TLS certificates?")
    ssl_verify: bool = chosen_ssl_verify.value

    proxy_dict = None
    proxy_url_input = fancy_input("HTTPS proxy URL (leave blank if not needed): ", loop=False)

    if proxy_url_input:
        proxy_dict = {'https', proxy_url_input}

    advanced_options_result = AdvancedOptionsType(cloud_name, ssl_verify, proxy_dict)
    return advanced_options_result
