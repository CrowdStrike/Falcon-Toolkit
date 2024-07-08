"""Falcon Toolkit: Host Search CLI.

This file contains the command line interface for the host_search command. The implementation
of the logic itself is contained in host_search.py
"""

import os

from typing import List

import click

from caracara.common.constants import OnlineState

from falcon_toolkit.common.cli import (
    get_instance,
    parse_cli_filters,
)
from falcon_toolkit.hosts.host_search import host_search_cmd


@click.command(
    name="host_search",
    help="List hosts within the environment without connecting to them",
)
@click.pass_context
@click.option(
    "-e",
    "--export",
    required=False,
    multiple=False,
    type=click.STRING,
    help="Export data to CSV, rather than output to screen, by providing a path to this parameter",
)
@click.option(
    "-f",
    "--filter",
    "filter_kv_strings",
    type=click.STRING,
    multiple=True,
    required=False,
    help="Filter hosts to search based on standard Falcon filters",
)
@click.option(
    "-o",
    "--online_state",
    "online_state",
    type=click.Choice(OnlineState.VALUES),
    multiple=False,
    required=False,
    help="Filter hosts by online state",
)
def cli_host_search(
    ctx: click.Context, filter_kv_strings: List[str], online_state: str = None, export: str = None
):
    """Implement the host_search CLI command."""
    instance = get_instance(ctx)
    client = instance.auth_backend.authenticate(ctx)
    filters = parse_cli_filters(filter_kv_strings, client)

    # Handle validation of the CSV export path here, before the search executes in host_search_cmd.
    # We only care here if the export parameter is not None; if it is None, we'll print the output
    # to screen.
    if export is not None:
        if not export.endswith(".csv"):
            click.echo(
                click.style(
                    f"{export} does not end in .csv. Please specify a filename ending in .csv.",
                    fg="red",
                )
            )
            return

        export_dirname = os.path.dirname(os.path.abspath(export))
        if not os.path.isdir(export_dirname):
            click.echo(
                click.style(
                    f"The directory {export_dirname} it not a valid directory. "
                    "Please create this directory before exporting host data to it.",
                    fg="red",
                )
            )
            return

    host_search_cmd(client, filters, online_state, export)
