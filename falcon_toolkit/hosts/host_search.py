"""Falcon Toolkit: Host Search.

This functionality allows users to search for hosts without connecting to them.
Once a set of filters has been decided upon, swapping 'host_search' for 'shell' at the CLI will
launch a batch RTR shell with these systems.
"""
import logging

import click
import click_spinner

from caracara import Client
from caracara.filters import FalconFilter


def host_search_cmd(
    client: Client,
    filters: FalconFilter,
):
    """Search for hosts that match the provided filters."""
    click.echo(click.style("Searching for hosts...", fg='magenta'))

    fql = filters.get_fql()

    with click_spinner.spinner():
        host_data = client.hosts.describe_devices(filters=fql)

    logging.debug(host_data)
    for aid in host_data.keys():
        hostname = host_data[aid].get("hostname", "<NO HOSTNAME>")
        click.echo(click.style(f"{hostname:16s}", fg='green'), nl=False)
        click.echo(f"- {aid}")
