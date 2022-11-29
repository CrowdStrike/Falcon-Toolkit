"""Falcon Toolkit: Configuration Backend.

Each instance configuration contains the logic required to log in to Falcon.
These configurations are stored in a wider config file stored within the configuration
path (usually ~/FalconToolkit/FalconToolkit.json).
"""
from __future__ import annotations
import importlib.util
import json
import os
import textwrap

from typing import Dict, List, Optional, TYPE_CHECKING

from colorama import Fore, Style

from falcon_toolkit.common.auth_backends.default import DEFAULT_AUTH_BACKENDS
from falcon_toolkit.common.constants import CONFIG_FILENAME
from falcon_toolkit.common.utils import fancy_input, fancy_input_int

if TYPE_CHECKING:
    from falcon_toolkit.common.auth import AuthBackend


AUTH_BACKENDS = [
    *DEFAULT_AUTH_BACKENDS,
]


class FalconInstanceConfig:
    """Contains all the data required to log in to a Falcon instance."""

    def __init__(self):
        """Set up a new Falcon instance."""
        self.auth_backend: Optional[AuthBackend] = None
        self.auth_config: Optional[Dict[str, str]] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None

    def __str__(self):
        """Return the name of the Falcon configuration profile."""
        return self.name

    def load_config(self, config: Dict[str, object]):
        """Load a Falcon instance from the configuration object."""
        self.name = config.get("name")
        if not self.name:
            raise KeyError("Invalid Falcon instance configuration: no name")

        self.description = config.get("description")

        auth = config.get("auth")
        if not auth:
            raise KeyError("Invalid Falcon instance configuration: no auth scection.")

        auth_backend_name = auth.get("backend_name")

        # Find the authentication backend with a matching simple_name
        matching_auth_backend = None
        for auth_backend in AUTH_BACKENDS:
            if auth_backend.simple_name == auth_backend_name:
                matching_auth_backend = auth_backend
                break

        if not matching_auth_backend:
            raise ValueError(
                f"Auth backend {auth_backend_name} is not loaded or does not exist"
            )

        auth_backend_config = auth.get("backend_config")
        if not auth_backend_config:
            raise KeyError("Auth backend configuration is empty")

        self.auth_backend = matching_auth_backend(config=auth_backend_config)

    def dump_config(self):
        """Return a dictionary representing the data required to store the instance config."""
        return {
            "name": self.name,
            "description": self.description,
            "auth": {
                "backend_name": self.auth_backend.simple_name,
                "backend_config": self.auth_backend.dump_config(),
            }
        }


class FalconToolkitConfig:
    """Contains the configuration for the loaded instance of the Falcon Toolkit."""

    additional_auth_backend_paths: List[str] = []
    config_file_path: Optional[str] = None
    instances: Dict[str, FalconInstanceConfig] = {}

    def init_additional_auth_backends(self):
        """Load additional configuration backends into the Toolkit via the JSON config."""
        for auth_backend_path in self.additional_auth_backend_paths:
            auth_backend_filename, _ = os.path.splitext(os.path.split(auth_backend_path)[-1])

            # Load the module from disk, execute it and then load the AuthBackend-derived class
            # Code adapted from:
            # https://www.edureka.co/community/95183/how-to-import-a-module-given-the-full-path
            auth_backend_spec = importlib.util.spec_from_file_location(
                auth_backend_filename,
                auth_backend_path,
            )
            auth_backend_module = importlib.util.module_from_spec(auth_backend_spec)
            auth_backend_spec.loader.exec_module(auth_backend_module)
            cls: AuthBackend = auth_backend_module.AuthBackend.__subclasses__()[-1]
            AUTH_BACKENDS.append(cls)

    def __init__(self, config_path: str):
        """Load a Falcon Toolkit configuration file from disk."""
        self.config_file_path = os.path.join(config_path, CONFIG_FILENAME)
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, 'rb') as config_file_handle:
                config_data = json.load(config_file_handle)
        else:
            config_data = {}

        self.additional_auth_backend_paths = config_data.get("auth_backends", [])
        self.init_additional_auth_backends()

        instance_configs: List[Dict[str, Dict]] = config_data.get("instances", [])
        for instance_config in instance_configs:
            new_instance = FalconInstanceConfig()
            new_instance.load_config(instance_config)
            self.instances[new_instance.name] = new_instance

        # Configure a description output wrapper for use in multiple functions
        self.desc_wrapper = textwrap.TextWrapper()
        self.desc_wrapper.width = 80
        self.desc_wrapper.initial_indent = "    "
        self.desc_wrapper.subsequent_indent = "    "

    def write_config(self):
        """Write an updated configuration object to disk."""
        config_data = {
            "auth_backends": self.additional_auth_backend_paths,
            "instances": [x.dump_config() for x in list(self.instances.values())],
        }
        with open(self.config_file_path, 'w', encoding='utf8') as config_file_handle:
            json.dump(config_data, config_file_handle, sort_keys=True, indent=4)

    def add_instance(self):
        """Create a new Falcon configuration profile."""
        print("Creating a new connection profile")
        new_instance = FalconInstanceConfig()
        new_instance.name = fancy_input("Instance name: ")
        new_instance.description = fancy_input("Instance description (optional): ", loop=False)

        if len(AUTH_BACKENDS) == 1:
            auth_backend: AuthBackend = AUTH_BACKENDS[0]
        else:
            print("Please choose an authentication backend from the following list: ")
            i = 0
            for backend_option in AUTH_BACKENDS:
                i += 1
                print(
                    f"{Fore.GREEN}"
                    f"{Style.BRIGHT}[{i}]{Style.NORMAL} "
                    f"{backend_option.name}"
                    f"{Fore.RESET}"
                )
                desc_lines = self.desc_wrapper.wrap(backend_option.description)
                for line in desc_lines:
                    print(line)

            valid_option = False
            while not valid_option:
                selected_option = fancy_input_int("Enter the option number: ")
                if selected_option <= len(AUTH_BACKENDS):
                    valid_option = True

            auth_backend: AuthBackend = AUTH_BACKENDS[selected_option - 1]

        new_instance.auth_backend = auth_backend()

        self.instances[new_instance.name] = new_instance

        self.write_config()

    def remove_instance(self, instance_name: str):
        """Delete a Falcon configuration profile."""
        if instance_name in self.instances:
            del self.instances[instance_name]
            self.write_config()
        else:
            print(f"{instance_name} is not a valid Falcon profile name")

    def list_instances(self):
        """List Falcon configuration profiles."""
        print("Falcon Instance Configurations")
        if self.instances:
            for instance_name, instance in self.instances.items():
                print(f"* {Fore.GREEN}{instance_name}{Fore.RESET}")
                if instance.description:
                    desc_lines = self.desc_wrapper.wrap(instance.description)
                    for line in desc_lines:
                        print(line)
        else:
            print("No Falcon tenants have been configured yet")
