"""Falcon Toolkit: Shell.

This file contains the CLI options for the shell command, which allows a user to invoke a batch
RTR shell with many connected systems at once.
"""
import logging
import logging.handlers
import sys

from typing import List

import click

from click_option_group import (
    optgroup,
    MutuallyExclusiveOptionGroup,
)

from falcon_toolkit.common.cli import (
    get_instance,
    parse_cli_filters,
)
from falcon_toolkit.shell.prompt import RTRPrompt


@click.command(
    name='shell',
    help='Create a Real Time Response batch shell',
)
@click.pass_context
@optgroup.group(
    "Specify devices",
    cls=MutuallyExclusiveOptionGroup,
    help="Choose no more than one method to choose systems to connect to"
)
@optgroup.option(
    '-d',
    '--device-id-list',
    'device_id_list',
    type=click.STRING,
    help="Specify a list of Device IDs (AIDs) to connect to, comma delimited",
)
@optgroup.option(
    '-df',
    '--device-id-file',
    'device_id_file',
    type=click.STRING,
    help=(
        "Specify a list of Device IDs (AIDs) to connect to in an external file, one per line; "
        "this can help you get round command line length limits in your workstation's shell,"
    ),
)
@optgroup.option(
    '-f',
    '--filter',
    'filter_kv_strings',
    type=click.STRING,
    multiple=True,
    help="Filter hosts to connect to based on standard Falcon filters",
)
@optgroup.group(
    "RTR Connection Options",
    help="General connection options for the Real Time Response (RTR) batch session."
)
@optgroup.option(
    '-q',
    '--queueing',
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Enable RTR Queueing  (default: off)",
)
@optgroup.option(
    '-s',
    '--script',
    'startup_script',
    required=False,
    type=click.STRING,
    help=(
        "Provide an RTR script file path to execute as soon as RTR connects. Note that, unless "
        "this script ends in the 'quit' command, the shell will remain open after completion. "
        "This command line switch is not required to run commands via stdin; just pipe straight "
        "into this tool to accomplish this."
    ),
)
@optgroup.option(
    '-t',
    '--timeout',
    type=click.INT,
    default=30,
    required=False,
    help="Set the timeout for RTR (default: 30s)",
)
def cli_shell(  # pylint: disable=too-many-arguments,too-many-locals
    ctx: click.Context,
    device_id_list: str,
    device_id_file: str,
    filter_kv_strings: List[str],
    queueing: bool,
    startup_script: str,
    timeout: int,
):
    """Implement the falcon shell command.

    When this CLI option is invoked, we get all the information needed to set up a batch shell
    within prompt.py.
    This includes:
    - Authenticating to Falcon via Caracara and the authentication backend provided within the
      profile's configuration
    - Loading a list of Device IDs to connect to from one of three places:
      -> Falcon, based on a list of filters provided via one or many -f switches
      -> Falcon, based on no filters or restrictions at all (i.e., connect to all hosts in a tenant)
      -> The CLI, based on a comma delimited list of Device IDs passed via a -d switch
      -> A file, based on a new-lien delimited list of Device IDs within a file, the name of which
         is passed to the CLI via the the -df switch
    - Configuring the output CSV for all commands to be logged to

    Once we have all the required information together, we configure an RTRPrompt object then
    start the REPL command loop. This passes control over to the shell, via the Cmd2 library.
    """
    instance = get_instance(ctx)
    client = instance.auth_backend.authenticate()

    if filter_kv_strings:
        click.echo(click.style(
            "Connecting to all hosts that match the provided Falcon filters",
            fg='magenta',
            bold=True,
        ))
        logging.info("Connecting to all hosts that match the provided Falcon filters")

        filters = parse_cli_filters(filter_kv_strings, client).get_fql()
        click.echo(click.style("FQL filter string: ", bold=True), nl=False)
        click.echo(filters)
        logging.info(filters)

        device_ids = client.hosts.get_device_ids(filters=filters)
    elif device_id_list:
        click.echo(click.style(
            "Connecting to the device IDs provided on the command line",
            fg='magenta',
            bold=True,
        ))
        logging.info("Connecting to the device IDs provided on the command line")

        device_ids = set()
        for device_id in device_id_list.split(","):
            device_id = device_id.strip()
            if device_id:
                device_ids.add(device_id)

        device_ids = list(device_ids)
    elif device_id_file:
        click.echo(click.style(
            "Connecting to the device IDs listed in a file",
            fg='magenta',
            bold=True,
        ))
        click.echo(click.style("File path: ", bold=True), nl=False)
        click.echo(device_id_file)
        logging.info("Connecting to the device IDs listed in %s", device_id_file)

        with open(device_id_file, 'rt', encoding='ascii') as device_id_file_handle:
            device_ids = set()
            for line in device_id_file_handle:
                line = line.strip()
                if line:
                    device_ids.add(line)
            device_ids = list(device_ids)
    else:
        click.echo(click.style(
            "WARNING: Connecting to all hosts in the Falcon instance",
            fg='yellow',
        ))
        logging.info("Connecting to all hosts in the Falcon instance")
        device_ids = client.hosts.get_device_ids()

    if not device_ids:
        click.echo(click.style("No devices match the provided filters", fg='red', bold=True))
        sys.exit(1)

    device_count = len(device_ids)
    click.echo(click.style(f"Connecting to {device_count} device(s)", bold=True))
    logging.info("Connecting to %d device(s)", device_count)
    logging.debug(device_ids)

    log_filename_base = ctx.obj['log_filename_base']
    csv_filename = f"{log_filename_base}.csv"

    prompt = RTRPrompt(
        client=client,
        device_ids=device_ids,
        csv_output_file=csv_filename,
        startup_script=startup_script,
        timeout=timeout,
        queueing=queueing,
    )
    prompt.cmdloop()
