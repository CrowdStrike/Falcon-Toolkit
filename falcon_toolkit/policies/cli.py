"""Falcon Toolkit: Policy Management.

This file contains the command line interface for the policies commands. The implementation
of the logic itself is contained in other files, including policies.py
"""
import json
import os

from typing import (
    List,
    Union,
)

import click
import pick

from caracara import Client
from caracara.common.policy_wrapper import Policy
from caracara.modules.prevention_policies import PreventionPoliciesApiModule
from caracara.modules.response_policies import ResponsePoliciesApiModule

from click_option_group import (
    optgroup,
    RequiredMutuallyExclusiveOptionGroup,
)

from falcon_toolkit.common.cli import get_instance
from falcon_toolkit.policies.describe import pretty_print_policies


PoliciesAPIModule = Union[
    PreventionPoliciesApiModule,
    ResponsePoliciesApiModule,
]


@click.group(
    name='policies',
    help='Manage Falcon Prevention and Response policies',
)
@click.pass_context
@optgroup.group(
    "Policy Type",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Choose whether to interface with [-p]revention or [-r]esponse policies",
)
@optgroup.option(
    '-p',
    '--prevention',
    'prevention_policies_option',
    is_flag=True,
    help="Interface with Prevention policies",
)
@optgroup.option(
    '-r',
    '--response',
    'response_policies_option',
    is_flag=True,
    help="Interface with Response policies",
)
def cli_policies(
    ctx: click.Context,
    prevention_policies_option: bool,
    response_policies_option: bool,
):
    """Configure the future profiles commands by getting the context in shape."""
    instance = get_instance(ctx)
    client: Client = instance.auth_backend.authenticate()
    ctx.obj['client'] = client

    if prevention_policies_option:
        ctx.obj['policies_api'] = client.prevention_policies
        ctx.obj['policies_type'] = "prevention"
    elif response_policies_option:
        ctx.obj['policies_api'] = client.response_policies
        ctx.obj['policies_type'] = "response"
    else:
        raise Exception("Impossible scenario: no policy type specified")


@click.command(
    name='describe',
    help='List and describe the policies within the Falcon tenant.'
)
@click.pass_context
def policies_describe(ctx: click.Context):
    """List and describe the Prevention or Response policies within the Falcon tenant."""
    policies_api: PoliciesAPIModule = ctx.obj['policies_api']
    policies_type: str = ctx.obj['policies_type']
    click.echo(click.style(f"Describing all {policies_type} policies", fg='green', bold=True))
    policies = policies_api.describe_policies()
    pretty_print_policies(policies)


@click.command(
    name='export',
    help='Export a Prevention or Response policy to disk.',
)
@click.pass_context
def policies_export(ctx: click.Context):
    """Allow a user to choose a Prevention or Response policy to export to disk."""
    # pylint: disable=too-many-locals
    policies_api: PoliciesAPIModule = ctx.obj['policies_api']
    policies_type: str = ctx.obj['policies_type']
    click.echo("Loading policies...")
    policies = policies_api.describe_policies()

    options: List[pick.Option] = []
    for policy in policies:
        option_text = f"{policy.name} [{policy.platform_name}]"
        option = pick.Option(label=option_text, value=policy)
        options.append(option)

    chosen_option, _ = pick.pick(options, "Please choose a policy to export")
    chosen_policy: Policy = chosen_option.value
    default_filename = f"{chosen_policy.name}.json"
    reasonable_filename = False
    while not reasonable_filename:
        filename: str = click.prompt("Policy filename", type=str, default=default_filename)
        if not filename.endswith(".json"):
            click.echo(click.style("Filename must end in .json", fg='yellow'))
            continue

        if os.path.exists(filename):
            click.echo(click.style("File already exists!", fg='yellow'))
            continue

        reasonable_filename = True

    policy_data = chosen_policy.flat_dump()

    export_data = {
        "format_version": 1,
        "name": chosen_policy.name,
        "platform_name": chosen_policy.platform_name,
        "policy_type": policies_type,
        "settings_key_name": chosen_policy.settings_key_name,
        "settings": policy_data[chosen_policy.settings_key_name],
    }
    with open(filename, 'wt', encoding='utf-8') as export_file_handle:
        json.dump(export_data, export_file_handle, indent=2)

    click.echo("Export complete")


@click.command(
    name='import',
    help='Import a Prevention or Response policy from disk.',
)
@click.pass_context
@click.argument(
    'filename',
    type=click.STRING,
)
def policies_import(
    ctx: click.Context,
    filename: str,
):
    """Import a Prevention or Response policy from the JSON file named FILENAME."""
    policies_api: PoliciesAPIModule = ctx.obj['policies_api']
    policies_type: str = ctx.obj['policies_type']
    with open(filename, 'rb') as policy_file_handle:
        policy_obj = json.load(policy_file_handle)

    new_policy = policies_api.new_policy(policy_obj['platform_name'])
    # TODO: Finish this function

cli_policies.add_command(policies_describe)
cli_policies.add_command(policies_export)
cli_policies.add_command(policies_import)
