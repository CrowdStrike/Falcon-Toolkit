"""Falcon Toolkit: Authentication Backend.

This code file contains the logic required to generalise the authentication methods for Caracara.
Each authentication backend has to be able to return a Caracara Client object, which itself will
hold a FalconPy authentication object. It will be possible to generate more of these backends for
other purposes, such as for authentication against alternative API gateways.
"""
from __future__ import annotations
from abc import (
    abstractmethod,
    ABC,
)
from typing import (
    Dict,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from caracara import Client


class AuthBackend(ABC):
    """Authentication Backend.

    This class is derived from to produce authentication handlers. Each of these handlers
    takes a series of parameters, and will return an OAuth2 object that can be used by
    FalconPy.
    """

    @property
    @abstractmethod
    def description(self) -> str:
        """Output a human readable description of the authentication backend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Define the name of the authentication backened, as shown to the user."""

    @property
    @abstractmethod
    def simple_name(self) -> str:
        """Define an ASCII name without spaces that is used in configuration files."""

    @abstractmethod
    def __init__(self, config: Dict = None):
        """Configure the authentiation backend based on a current configuration.

        If more information is needed from the user, this will be requested here.
        """

    @abstractmethod
    def authenticate(self) -> Client:
        """Return a complete OAuth2 object, ready for use with FalconPy."""

    @abstractmethod
    def dump_config(self) -> Dict[str, object]:
        """Export the configuration variables ready for writing to the config file."""
