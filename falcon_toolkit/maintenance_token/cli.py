"""Falcon Toolkit: Maintenance Token Retrieval.

This file contains the CLI options for the falcon maintenance_token command.
"""

import logging

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
from falcon_toolkit.maintenance_token.device_tokens import show_device_maintenance_tokens


@click.command(
    name="maintenance_token",
    help="Get the maintenance token for a device, or get the bulk maintenance token",
)
@click.pass_context
@optgroup.group(
    "Specify devices to get the token for",
    cls=MutuallyExclusiveOptionGroup,
    help="Choose no more than one method to choose systems to fetch the maintenance tokens for",
)
@optgroup.option(
    "-b",
    "--bulk",
    "bulk_token",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Get the CID-wide bulk maintenance token",
)
@optgroup.option(
    "-d",
    "--device-id-list",
    "device_id_list",
    type=click.STRING,
    help="Specify a list of Device IDs (AIDs), comma delimited",
)
@optgroup.option(
    "-df",
    "--device-id-file",
    "device_id_file",
    type=click.STRING,
    help=(
        "Specify a list of Device IDs (AIDs) in an external file, one per line; "
        "this can help you get round command line length limits in your workstation's shell,"
    ),
)
@optgroup.option(
    "-f",
    "--filter",
    "filter_kv_string",
    type=click.STRING,
    multiple=True,
    help="Filter hosts based on standard Falcon filters",
)
def cli_maintenance_token(
    ctx: click.Context,
    bulk_token: bool,
    device_id_list: str,
    device_id_file: str,
    filter_kv_string: List[str],
):
    """Get system maintenance tokens from Falcon."""
    instance = get_instance(ctx)
    client: Client = instance.auth_backend.authenticate(ctx)
    ctx.obj["client"] = client

    # Bulk token is a special case we can handle here.
    # Device tokens need to be handled elsewhere.
    if bulk_token:
        click.echo(
            click.style(
                "Getting the bulk maintenance token",
                fg="magenta",
                bold=True,
            )
        )
        token = client.sensor_update_policies.get_bulk_maintenance_token(
            audit_message="Fetched via Falcon Toolkit",
        )
        click.echo("Bulk maintenance token: ", nl=False)
        click.echo(click.style(token, bold=True, fg="blue"))
        click.echo(
            click.style(
                "WARNING: this token must be kept safe, as it can uninstall all Falcon sensors!",
                bold=True,
                fg="red",
            )
        )

        return

    if filter_kv_string:
        click.echo(
            click.style(
                "Getting the maintenance tokens for all hosts that match the provided"
                " Falcon filters",
                fg="magenta",
                bold=True,
            )
        )
        logging.info("Getting maintenance tokens for all devices that match the provided filters")

        filters = parse_cli_filters(filter_kv_string, client).get_fql()
        click.echo(click.style("FQL filter string: ", bold=True), nl=False)
        click.echo(filters)
        logging.info(filters)

        device_ids = client.hosts.get_device_ids(filters=filters)

    elif device_id_list:
        click.echo(
            click.style(
                "Getting the maintenance tokens for the devices identified by the IDs provided on "
                "the command line",
                fg="magenta",
                bold=True,
            )
        )
        logging.info(
            "Getting the maintenance tokens for the devices identified by the IDs "
            "provided on the command line"
        )

        device_ids = set()
        for device_id in device_id_list.split(","):
            device_id = device_id.strip()
            if device_id:
                device_ids.add(device_id)

    elif device_id_file:
        click.echo(
            click.style(
                "Getting the maintenance tokens for the devices identified by the IDs listed in a"
                " file",
                fg="magenta",
                bold=True,
            )
        )
        click.echo(click.style("File path: ", bold=True), nl=False)
        click.echo(device_id_file)
        logging.info(
            "Getting the maintenance tokens for the devices identified by the IDs listed in %s",
            device_id_file,
        )

        with open(device_id_file, "rt", encoding="ascii") as device_id_file_handle:
            device_ids = set()
            for line in device_id_file_handle:
                line = line.strip()
                if line:
                    device_ids.add(line)

    else:
        click.echo(
            click.style(
                "Getting the maintenance token for all systems in the tenant!",
                bold=True,
                fg="yellow",
            )
        )
        click.echo('You must enter the string "I AM SURE!" to proceed.')
        confirmation = input("Are you sure? ")
        if confirmation != "I AM SURE!":
            print("You did not confirm you were sure. Aborting!")
            return

        device_ids = client.hosts.get_device_ids()

    logging.debug(device_ids)
    if device_ids:
        show_device_maintenance_tokens(
            device_ids=device_ids,
            client=client,
        )
    else:
        click.echo(
            click.style(
                "No devices matched the provided filters",
                fg="red",
                bold=True,
            )
        )
