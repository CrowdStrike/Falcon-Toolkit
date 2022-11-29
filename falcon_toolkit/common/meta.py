"""Falcon Toolkit: Meta.

This is where all functions and variable setting that are based on application metadata live.
"""

import pkg_resources

# Derive the version via pkg_resources, which is populated based on the version in pyproject.toml
__version__ = pkg_resources.get_distribution(
    __name__.split(".", maxsplit=1)[0]
).version
