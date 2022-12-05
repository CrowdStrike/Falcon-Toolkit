"""Falcon Toolkit: Policy Management.

This file contains constants that are required to properly display and manage Prevention and
Response policies within a Falcon tenant.
"""
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
