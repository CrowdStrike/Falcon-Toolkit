"""Falcon Toolkit: Containment.

This file contains the logic required to contain and uncontain systems.
"""
import logging

from operator import itemgetter
from typing import Dict, List, Optional, Union

import click
import tabulate

from caracara import Client


def result_output(
    resources: Optional[List[Dict[str, str]]],
    errors: Optional[List[Dict[str, Union[str, int]]]],
):
    """Visually show the output of the containment action via tabulate."""
    # If we had no successes and no errors, we bail out
    if not resources and not errors:
        return

    header_row = [
        click.style("Device ID", bold=True, fg='blue'),
        click.style("Result", bold=True, fg='blue'),
    ]
    results_table = [header_row]

    # Handle the successes first
    if resources:
        success_rows = []
        for resource in resources:
            success_rows.append([
                resource['id'],
                click.style("Success", fg='green'),
            ])

        success_rows = sorted(success_rows, key=itemgetter(1, 0))
        results_table.extend(success_rows)

    if errors:
        error_rows = []
        for error in errors:
            code = error['code']
            message = error['message']

            if message.startswith("Device "):
                device_id = message.split(" ")[1]
            else:
                device_id = "Unknown"

            result_text = click.style("Failed", fg='red')
            if code == 409:
                result_text += ": incompatible current containment state"
            else:
                result_text += f": {message} (code: {code})"

            error_rows.append([
                device_id,
                result_text,
            ])

        error_rows = sorted(error_rows, key=itemgetter(1, 0))
        results_table.extend(error_rows)

    click.echo(tabulate.tabulate(
        results_table,
        tablefmt='fancy_grid',
    ))


def perform_containment_action(
    device_ids: List[str],
    client: Client,
    action: str = "contain",
):
    """Contain or uncontain a batch of systems and visually report the result."""
    logging.debug("Performing a containment action: %s", action)

    if action not in ("contain", "lift_containment"):
        raise ValueError(f"{action} is not a supported device action in this function")

    limit = 100
    resources = []
    errors = []

    for i in range(0, len(device_ids), limit):
        click.echo("Changing the network containment status on a batch of systems...", nl=False)
        response = client.hosts.hosts_api.perform_action(
            action_name=action,
            ids=device_ids[i: i + limit],
        )
        logging.debug(response)

        if response['status_code'] == 202:
            click.echo(click.style("Succeeded", fg='green'))
        elif 'resources' in response['body'] and response['body']['resources']:
            click.echo(click.style("Partially succeeded", fg='yellow'))
        else:
            click.echo(click.style("Failed", fg='red'))

        batch_resources = response['body'].get("resources")
        if batch_resources:
            resources.extend(batch_resources)

        batch_errors = response['body'].get("errors")
        if batch_errors:
            errors.extend(batch_errors)

    result_output(resources, errors)
