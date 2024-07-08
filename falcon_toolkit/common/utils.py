"""Falcon Toolkit: Common Utils.

This file is a catch-all for small code snippets that can be shared across the various sub-modules
of the application.
"""

import os

from typing import Dict, Iterable

from colorama import (
    Fore,
    Style,
)
from prompt_toolkit import prompt
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from falcon_toolkit.common.constants import LOG_SUB_DIR


def fancy_input(prompt_text: str, loop: bool = True):
    """Request user input (with colour). Optionally loop until the input is not blank."""
    inputted = False
    colour_prompt = Style.BRIGHT + Fore.BLUE + prompt_text + Fore.RESET + Style.RESET_ALL

    while not inputted:
        data = input(colour_prompt)
        if data or not loop:
            inputted = True

    return data


def fancy_input_int(prompt_text: str) -> int:
    """Request an integer from the user (with colour), and loop until the input is valid."""
    valid_input = False
    while not valid_input:
        typed_input = fancy_input(prompt_text, loop=True)
        if typed_input.isdigit():
            valid_input = True

    return int(typed_input)


def configure_data_dir(config_dir: str):
    """Configure the Falcon Toolkit data directory with a directory skeleton."""
    if os.path.exists(config_dir):
        if not os.path.isdir(config_dir):
            raise ValueError("Specified configuration directory path is already a file")
    else:
        os.makedirs(config_dir)

    logs_path = os.path.join(config_dir, LOG_SUB_DIR)
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)


def filename_safe_string(unsafe_string: str) -> str:
    """Convert an unsafe string to one that can be included in a filename.

    This function is heavily inspired by https://stackoverflow.com/a/7406369.
    """
    safe_string = "".join(
        [c for c in unsafe_string if c.isalpha() or c.isdigit() or c == " "]
    ).rstrip()

    # Replace spaces with underscores to match the general format of the log filename
    clean_string = safe_string.replace(" ", "_")

    return clean_string


class CIDCompleter(Completer):
    """Prompt Toolkit Completer that provides a searchable list of CIDs."""

    def __init__(self, data_dict: Dict[str, Dict]):
        """Create a new CID completer based on a dictionary that maps CIDs to meta strings."""
        self.data_dict = data_dict

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        """Yield CIDs that match the entered search string."""
        for cid, cid_data in self.data_dict.items():
            cid_name = cid_data["name"]
            cloud_name = cid_data.get("cloud_name")
            if cloud_name:
                display_meta = f"{cid_name} [{cloud_name}]"
            else:
                display_meta = cid_name

            word_lower = document.current_line.lower()
            if word_lower in cid or word_lower in display_meta.lower():
                yield Completion(
                    cid,
                    start_position=-len(document.current_line),
                    display=cid,
                    display_meta=display_meta,
                )


def choose_cid(cids: Dict[str, Dict], prompt_text="CID Search") -> str:
    """Choose a CID from a dictionary of CIDs via Prompt Toolkit and return the CID string."""
    cid_completer = CIDCompleter(data_dict=cids)
    chosen_cid = None
    while chosen_cid not in cids:
        chosen_cid = prompt(f"{prompt_text} >", completer=cid_completer)

    print(chosen_cid)
    return chosen_cid
