"""Falcon Toolkit: Containment.

This file contains the CLI options for the falcon containment commands.
"""
import logging
import sys

from typing import List

import click

from caracara import Client
from click_option_group import (
    optgroup,
    MutuallyExclusiveOptionGroup,
)

from falcon_toolkit.common.cli import (
    get_instance,
    parse_cli_filters,
)
from falcon_toolkit.containment.perform_containment import perform_containment_action


@click.group(
    name='containment',
    help="Manage the containment status of systems in a CID",
)
@click.pass_context
@optgroup.group(
    "Specify devices",
    cls=MutuallyExclusiveOptionGroup,
    help="Choose no more than one method to choose systems to contain or uncontain"
)
@optgroup.option(
    '-d',
    '--device-id-list',
    'device_id_list',
    type=click.STRING,
    help="Specify a list of Device IDs (AIDs), comma delimited"
)
@optgroup.option(
    '-df',
    '--device-id-file',
    'device_id_file',
    type=click.STRING,
    help=(
        "Specify a list of Device IDs (AIDs) in an external file, one per line; "
        "this can help you get round command line length limits in your workstation's shell,"
    ),
)
@optgroup.option(
    '-f',
    '--filter',
    'filter_kv_string',
    type=click.STRING,
    multiple=True,
    help="Filter hosts based on standard Falcon filters",
)
def cli_containment(
    ctx: click.Context,
    device_id_list: str,
    device_id_file: str,
    filter_kv_string: List[str],
):
    """Manage the containment status of hosts in Falcon."""
    instance = get_instance(ctx)
    client: Client = instance.auth_backend.authenticate()
    ctx.obj['client'] = client

    device_ids = None
    params = True

    if filter_kv_string:
        click.echo(click.style(
            "Managing all hosts that match the provided Falcon filters",
            fg='magenta',
            bold=True,
        ))
        logging.info(
            "Managing the containment status of all hosts that match the "
            "provided Falcon filters"
        )

        filters = parse_cli_filters(filter_kv_string, client).get_fql()
        click.echo(click.style("FQL filter string: ", bold=True), nl=False)
        click.echo(filters)
        logging.info(filters)

        device_ids = client.hosts.get_device_ids(filters=filters)

    elif device_id_list:
        click.echo(click.style(
            "Managing the devices identified by the IDs provided on the command line",
            fg='magenta',
            bold=True,
        ))
        logging.info("Managing the devices identified by the IDs provided on the command line")

        device_ids = set()
        for device_id in device_id_list.split(","):
            device_id = device_id.strip()
            if device_id:
                device_ids.add(device_id)

    elif device_id_file:
        click.echo(click.style(
            "Managing the devices identified by the IDs listed in a file",
            fg='magenta',
            bold=True,
        ))
        click.echo(click.style("File path: ", bold=True), nl=False)
        click.echo(device_id_file)
        logging.info("Managing the devices identified by the IDs listed in %s", device_id_file)

        with open(device_id_file, 'rt', encoding='ascii') as device_id_file_handle:
            device_ids = set()
            for line in device_id_file_handle:
                line = line.strip()
                if line:
                    device_ids.add(line)
    else:
        params = False

    if params and device_ids is None:
        click.echo(click.style(
            "No devices matched the provided filters",
            fg='red',
            bold=True,
        ))
        sys.exit(1)

    ctx.obj['device_ids'] = device_ids


def check_empty_device_ids(client) -> List[str]:
    """Confirm with the user whether all devices should be managed.

    This function has been split out from the group as group parameters are evaluated first,
    before the individual command parameters. This means that if the user accidentally provides
    the filter parameters after the individual commands, rather than before, they'll need to
    write I AM SURE! before being told about their mistake.

    This therefore shifts the user logic to after the group parameters have been evaluated to
    improve the user experience and avoid confusion.
    """
    click.echo(click.style(
        "You did not specify any parameters. This command will manage the containment "
        "status of ALL devices in the Falcon tenant!",
        fg='yellow',
    ))

    click.echo("You must enter the string \"I AM SURE!\" to proceed.")
    confirmation = input("Are you sure? ")
    if confirmation != "I AM SURE!":
        print("You did not confirm you were sure. Aborting!")
        sys.exit(1)

    logging.info("Managing all hosts in the Falcon tenant")
    device_ids = client.hosts.get_device_ids()
    return device_ids


@cli_containment.command(
    name='contain',
    help='Network contain systems in a Falcon tenant',
)
@click.pass_context
def contain(ctx: click.Context):
    """Network contain systems."""
    client: Client = ctx.obj['client']
    device_ids: List[str] = ctx.obj['device_ids']

    if device_ids is None:
        device_ids = check_empty_device_ids(client)

    click.echo(f"Network containing {len(device_ids)} systems.")

    perform_containment_action(
        device_ids=device_ids,
        client=client,
        action="contain",
    )


@cli_containment.command(
    name='uncontain',
    help='Lift network containment from systems in a Falcon tenant',
)
@click.pass_context
def uncontain(ctx: click.Context):
    """Lift network containment on systems."""
    client: Client = ctx.obj['client']
    device_ids: List[str] = ctx.obj['device_ids']

    if device_ids is None:
        device_ids = check_empty_device_ids(client)

    click.echo(f"Lifting network containment on {len(device_ids)} systems.")

    perform_containment_action(
        device_ids=device_ids,
        client=client,
        action="lift_containment",
    )
