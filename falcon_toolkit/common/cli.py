"""Falcon Toolkit: Common CLI Functions."""
import sys

from typing import List

import click

from caracara import Client
from caracara.filters import FalconFilter

from falcon_toolkit.common.config import FalconToolkitConfig


def get_instance(ctx: click.Context):
    """Load a specified Falcon instance configuration ready for use."""
    config: FalconToolkitConfig = ctx.obj['config']
    profile_name: str = ctx.obj['profile_name']

    if profile_name in config.instances:
        profile = config.instances[profile_name]
    elif not profile_name and len(config.instances) == 1:
        profile = list(config.instances.values())[0]
    elif not config.instances:
        click.echo(click.style("No profiles are configured. Please set one up first.", fg='red'))
        sys.exit(1)
    elif not profile_name:
        click.echo(click.style(
            "Multiple profiles are configured, so you must use the -p/--profile option "
            "to choose a profile to execute this tool with.",
            fg='red',
        ))
        sys.exit(1)
    else:
        click.echo(click.style(f"The profile {profile_name} does not exist.", fg='red'))
        sys.exit(1)

    return profile


def parse_cli_filters(filter_kv_strings: List[str], client: Client) -> FalconFilter:
    """Parse consecutive chains of -f filters into a FalconFilter object for later use."""
    filters = client.FalconFilter()
    for filter_kv_string in filter_kv_strings:
        if '=' not in filter_kv_string:
            raise ValueError("Filter key=value string is in the wrong format")
        first_equals = filter_kv_string.index("=")
        filter_key = filter_kv_string[0:first_equals]
        filter_value = filter_kv_string[first_equals + 1:]
        filters.create_new_filter_from_kv_string(filter_key, filter_value)

    return filters
