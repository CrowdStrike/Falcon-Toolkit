"""Falcon Toolkit: Meta.

This is where all functions and variable setting that are based on application metadata live.
"""

import importlib.metadata

# Derive the version via importlib.metadata, which is populated based on the version in
# pyproject.toml. We used to use pkg_resources for this, but using importlib.metadata means
# that setuptools is no longer required.
__version__ = importlib.metadata.version("falcon-toolkit")
