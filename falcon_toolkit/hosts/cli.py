"""Falcon Toolkit: Host Search CLI.

This file contains the command line interface for the host_search command. The implementation
of the logic itself is contained in host_search.py
"""

from typing import List

import click

from falcon_toolkit.common.cli import (
    get_instance,
    parse_cli_filters,
)
from falcon_toolkit.hosts.host_search import host_search_cmd


@click.command(
    name='host_search',
    help='List hosts within the environment without connecting to them',
)
@click.pass_context
@click.option(
    '-f',
    '--filter',
    'filter_kv_strings',
    type=click.STRING,
    multiple=True,
    required=False,
    help="Filter hosts to search based on standard Falcon filters",
)
def cli_host_search(
    ctx: click.Context,
    filter_kv_strings: List[str],
):
    """Implement the host_search CLI command."""
    instance = get_instance(ctx)
    client = instance.auth_backend.authenticate()
    filters = parse_cli_filters(filter_kv_strings, client)

    host_search_cmd(client, filters)
