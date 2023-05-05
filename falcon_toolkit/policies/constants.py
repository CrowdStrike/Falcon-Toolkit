"""Falcon Toolkit: Policy Management.

This file contains constants that are required to properly display and manage Prevention and
Response policies within a Falcon tenant.
"""
from typing import Union

from caracara.modules.prevention_policies import PreventionPoliciesApiModule
from caracara.modules.response_policies import ResponsePoliciesApiModule
from colorama import Fore


ASCII_OFF_BUTTON = (
    f"{Fore.RED}-----------{Fore.RESET}\n"
    f"{Fore.RED}|   OFF   |{Fore.RESET}\n"
    f"{Fore.RED}-----------{Fore.RESET}\n"
)
ASCII_ON_BUTTON = (
    f"{Fore.GREEN}-----------{Fore.RESET}\n"
    f"{Fore.GREEN}|   ON    |{Fore.RESET}\n"
    f"{Fore.GREEN}-----------{Fore.RESET}\n"
)

# List of policy types as strings for a quick reference
POLICY_TYPES = [
    "prevention",
    "response",
]

# Union type of all types of all Caracara modules providing policy data
# They all expose a common API, so can be assumed to be one type where convenient
PoliciesApiModule = Union[
    PreventionPoliciesApiModule,
    ResponsePoliciesApiModule,
]
