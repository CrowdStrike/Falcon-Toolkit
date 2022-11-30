"""Falcon Toolkit: Common Utils.

This file is a catch-all for small code snippets that can be shared across the various sub-modules
of the application.
"""
import os

from colorama import (
    Fore,
    Style,
)

from falcon_toolkit.common.constants import LOG_SUB_DIR


def fancy_input(prompt: str, loop: bool = True):
    """Request user input (with colour). Optionally loop until the input is not blank."""
    inputted = False
    colour_prompt = Style.BRIGHT + Fore.BLUE + \
        prompt + Fore.RESET + Style.RESET_ALL

    while not inputted:
        data = input(colour_prompt)
        if data or not loop:
            inputted = True

    return data


def fancy_input_int(prompt: str) -> int:
    """Request an integer from the user (with colour), and loop until the input is valid."""
    valid_input = False
    while not valid_input:
        typed_input = fancy_input(prompt, loop=True)
        if typed_input.isdigit():
            valid_input = True

    return int(typed_input)


def configure_data_dir(config_dir: str):
    """Configure the Falcon Toolkit data directory with a directory skeleton."""
    if os.path.exists(config_dir):
        if not os.path.isdir(config_dir):
            raise ValueError("Specified configuration directory path is already a file")
    else:
        os.mkdir(config_dir)

    logs_path = os.path.join(config_dir, LOG_SUB_DIR)
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)


def filename_safe_string(unsafe_string: str) -> str:
    """Convert an unsafe string to one that can be included in a filename.

    This function is heavily inspired by https://stackoverflow.com/a/7406369.
    """
    safe_string = "".join(
        [c for c in unsafe_string if c.isalpha() or c.isdigit() or c == ' ']
    ).rstrip()

    # Replace spaces with underscores to match the general format of the log filename
    clean_string = safe_string.replace(' ', '_')

    return clean_string
