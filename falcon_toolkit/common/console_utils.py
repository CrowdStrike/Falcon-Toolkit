"""Falcon Toolkit: Console Utils.

This file contains tools to help with displaying data on the console in a user-friendly,
colourful and/or helpful way.
"""
import platform


ESC = '\033'
OSC = ESC + ']'
ST = ESC + '\\'


def build_hyperlink(target: str, text: str, link_id: str = None):
    """Build a clickable hyperlink that is compatible with modern shells."""
    if link_id:
        id_str = "id=" + link_id
    else:
        id_str = ""
    return f'{OSC}8;{id_str};{target}{ST}{text}{OSC}8;;{ST}'


def build_file_hyperlink(file_path: str, text: str, link_id: str = None):
    """Extend the build_hyperlink function to support file paths, cross-platform."""
    if platform.system() == "Windows":
        hostname = "localhost"
    else:
        hostname = platform.node()

    if file_path.startswith('/'):
        file_path = file_path[1:]

    uri_file_path = f"file://{hostname}/{file_path}"
    return build_hyperlink(uri_file_path, text, link_id)
