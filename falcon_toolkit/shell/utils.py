"""Falcon Toolkit: Shell Utilities.

This file contains helper functions for the main shell.
"""
import os

from caracara.modules.rtr import GetFile


def output_file_name(get_file: GetFile, hostname: str):
    """Create an output filename with the hostname in it."""
    if get_file.filename.startswith("/"):
        # macOS or *nix path
        filename = get_file.filename.rsplit("/", maxsplit=1)[-1]
    else:
        # Windows path
        filename = get_file.filename.rsplit("\\", maxsplit=1)[-1]

    filename_noext, ext = os.path.splitext(filename)

    final_filename = f'{filename_noext}_{hostname}_{get_file.device_id}_{get_file.sha256}{ext}'

    return final_filename
