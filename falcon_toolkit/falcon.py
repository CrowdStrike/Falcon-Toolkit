#!/usr/bin/env python3
"""Falcon Toolkit: Command Line Interface.

This code file contains the code required to make the falcon command work at the CLI.
The cli object below gets called when falcon is executed at the user's shell. This is handled by
Poetry and/or setuptools.

We use click as our CLI builder of choice for its extensibility. Adding new root commands according
to this defined structure requires creating something like this:
/falcon_toolkit
    /new_command
        /cli.py
Within each cli.py you should have a click command that is imported below. This helps to keep
falcon.py small, whilst providing plenty of extensibility later.
Whilst we could dynamically load these falcon CLI commands via reflection, it is faster, more
maintainable and easier on code linters to just manually import everything below.

The cli function below is invoked when the user calls the falcon command, and it performs
the following steps:
- Initialises Colorama, which gives us multicoloured output support outside of click.echo
    (this is used a lot in the shell, where we do not use Click as much)
- Outputs a standard string to let the user know that the Toolkit is in charge here
- Loads a configuration JSON file from disk
- Configures a passable context dictionary (ctx.obj) that can be loaded and used by each
    Click CLI command, as needed
- Configures a global logger
"""
import logging
import os

import click

from caracara.filters.fql import FalconFilterAttribute
from caracara.modules.hosts import FILTER_ATTRIBUTES as HOSTS_FILTER_ATTRIBUTES
from colorama import (
    deinit as colorama_deinit,
    init as colorama_init,
)

from falcon_toolkit.common.config import FalconToolkitConfig
from falcon_toolkit.common.constants import (
    DEFAULT_CONFIG_DIR,
    LOG_SUB_DIR,
)
from falcon_toolkit.common.console_utils import build_file_hyperlink
from falcon_toolkit.common.logging_config import configure_logger
from falcon_toolkit.common.utils import configure_data_dir
from falcon_toolkit.hosts.cli import cli_host_search
from falcon_toolkit.shell.cli import cli_shell


@click.group()
@click.pass_context
@click.option(
    '-c',
    '--config-path',
    envvar='FALCON_TOOLKIT_CONFIG_DIR',
    type=click.STRING,
    default=DEFAULT_CONFIG_DIR,
    help="Path to the configuration directory (default: ~/.FalconToolkit/)",
)
@click.option(
    '-v',
    '--verbose',
    envvar='FALCON_TOOLKIT_VERBOSE',
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Enable info-level logging at the CLI",
)
@click.option(
    '-p',
    '--profile',
    envvar='FALCON_TOOLKIT_PROFILE',
    type=click.STRING,
    default=None,
    help=(
        "Select a profile to execute the Falcon Toolkit against. If you only have one "
        "profile (Falcon Tenant) set up, this parameter is not required."
    ),
)
def cli(
    ctx: click.Context,
    config_path: str,
    verbose: bool,
    profile: str,
):
    r"""Falcon Toolkit.

    The Falcon Toolkit is a handy command line interface (CLI) tool that can help you interface
    with your Falcon instance more quickly.

    To get started, create a profile using the falcon profiles new command. For futher help,
    you can always add the --help switch on to a command, like this:

        $ falcon profiles --help

    General Toolkit options are shown below, and should be provided after the Falcon command.
    Command-specific options should be provided after the command's name. More generically,
    Falcon Toolkit commands should be written like this:

        $ falcon [General Options] [Command] [Command-Specific Options]

    For example, to connect to a Falcon tenant via a profile named ACME, in verbose mode, and
    then drop to a shell with every Windows system that is a server or domain controller,
    type this command:

                   Command -- \/   \/ ---- Command Options ---- \/

            $ falcon -p ACME shell -f OS=Windows -f Role=Server,DC

    This tool --^         ^-- General Option
    """
    # Enable colorama across the board
    colorama_init(autoreset=True)

    # Configure context that can be passed down to other options
    ctx.ensure_object(dict)
    click.echo(click.style("Falcon Toolkit", fg='blue', bold=True))
    config_path = os.path.expanduser(config_path)
    hyperlink = build_file_hyperlink(config_path, config_path, "falcon_config_path")
    click.echo(click.style(f"Configuration Directory: {hyperlink}", fg='black'))
    if verbose:
        log_level = logging.INFO
    else:
        log_level = logging.CRITICAL

    # Configure and load the configuration object
    configure_data_dir(config_path)
    config = FalconToolkitConfig(config_path=config_path)
    ctx.obj['config'] = config

    # Configure the logger
    log_path = os.path.join(config_path, LOG_SUB_DIR)
    log_filename_base = configure_logger(
        log_path=log_path,
        profile_name=profile,
        log_level=log_level,
        log_compression=True,
    )
    ctx.obj['log_filename_base'] = log_filename_base

    # Pass a profile name down the chain in case one is selected
    ctx.obj['profile_name'] = profile


@cli.result_callback()
def cli_process_result(  # pylint: disable=unused-argument
    result,
    **kwargs,
):
    """Handle any necessary cleanup once the toolkit terminates.

    Right now, we just ensure that we clean up Colorama at the end of execution to avoid impacting
    the shell that invoked us.
    """
    colorama_deinit()


@cli.group(
    help='Show, create and delete Falcon Toolkit connection profiles',
)
def profiles():
    """Root command group to handle connection profiles."""


@profiles.command(
    name='delete',
    help="Delete a Falcon connection profile.",
)
@click.pass_context
@click.argument(
    'profile_name',
    type=click.STRING,
)
def profiles_delete(
    ctx: click.Context,
    profile_name: str,
):
    """Delete a connection profile."""
    click.echo(f"Deleting {profile_name}")
    config: FalconToolkitConfig = ctx.obj['config']
    config.remove_instance(profile_name)


@profiles.command(
    name='list',
    help="List Falcon connection profiles.",
)
@click.pass_context
def profiles_list(ctx: click.Context):
    """Show all connection profiles that exist within the current configuration."""
    config: FalconToolkitConfig = ctx.obj['config']
    config.list_instances()


@profiles.command(
    name='new',
    help="Create a new Falcon connection profile.",
)
@click.pass_context
def profiles_new(ctx: click.Context):
    """Create a new profile, based on all loaded authentication backends."""
    click.echo("New profile")
    config: FalconToolkitConfig = ctx.obj['config']
    config.add_instance()


@click.command(
    name='filters',
    help='Get information on available filters',
)
def cli_list_filters():
    """List all possible filters out on screen based on data available within Caracara."""
    for hosts_filter_attribute in HOSTS_FILTER_ATTRIBUTES:
        hosts_filter_attribute_obj: FalconFilterAttribute = hosts_filter_attribute()
        click.echo(click.style(hosts_filter_attribute_obj.name, fg='blue', bold=True))
        click.echo(click.style(hosts_filter_attribute_obj.description, dim=True))
        click.echo(hosts_filter_attribute_obj.example())

        click.echo()


# Load all commands into the main cli object, ready for use as root falcon commands
cli.add_command(cli_shell)
cli.add_command(cli_host_search)
cli.add_command(cli_list_filters)
