"""Falcon Toolkit: Maintenance Token Retrieval.

This file contains the logic required to fetch tokens for many devices and write them to screen.
"""
import logging

from operator import itemgetter
from typing import List

import click
import click_spinner
import tabulate

from caracara import Client


def show_device_maintenance_tokens(
    device_ids: List[str],
    client: Client,
):
    """Get maintenance tokens for many devices and print them to screen."""
    click.echo("Fetching requested maintenance tokens. This may take a while.")

    tokens = {}
    header_row = [
        click.style("Device ID", bold=True, fg='blue'),
        click.style("Maintenance Token", bold=True, fg='blue'),
    ]
    tokens_table = []

    with click_spinner.spinner():
        for device_id in device_ids:
            token = client.sensor_update_policies.get_maintenance_token(
                device_id=device_id,
                audit_message="Fetched via Falcon Toolkit",
            )
            logging.debug("%s -> %s", device_id, token)
            tokens[device_id] = token
            tokens_table.append([
                device_id,
                token,
            ])

    tokens_table = sorted(tokens_table, key=itemgetter(1, 0))
    tokens_table.insert(0, header_row)
    click.echo(tabulate.tabulate(
        tokens_table,
        tablefmt='fancy_grid',
    ))
