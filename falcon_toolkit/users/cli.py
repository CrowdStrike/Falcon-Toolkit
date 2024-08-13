"""Falcon Toolkit: User Modification.

This file contains the CLI options for the falcon user modification commands.
"""

from os import path

import click
from caracara import Client
from prompt_toolkit import prompt

from falcon_toolkit.users.user_management import (
    user_deletion,
    add_csv_users,
    add_single_user,
    add_roles_to_user,
    print_formatted_user_roles,
    describe_existing_users,
)
from falcon_toolkit.common.cli import get_instance


@click.group(
    name="users",
    help="Manage Falcon User Creation and Deletion",
)
@click.pass_context
def cli_users(ctx: click.Context):
    """Falcon Toolkit user management base command."""
    instance = get_instance(ctx)
    client: Client = instance.auth_backend.authenticate(ctx)
    ctx.obj["client"] = client


@click.command(
    name="add_user",
    help="Create users via CLI inputs",
)
@click.pass_context
def add_user(ctx: click.Context):
    """Create a new user in the Falcon tenant."""
    single_email = prompt("Enter the new user's email address: ")
    first_name = prompt(f"Enter {single_email}'s first name: ")
    last_name = prompt(f"Enter {single_email}'s last name: ")
    add_single_user(ctx.obj["client"], first_name, last_name, single_email)


@click.command(
    name="import_users",
    help="Create users from a CSV file formatted first_name,last_name,email_address",
)
@click.argument("csv_file")
@click.pass_context
def import_users(ctx: click.Context, csv_file):
    """Create users and set their roles in the Falcon tenant from a CSV file."""
    if path.isfile(csv_file):
        add_csv_users(ctx.obj["client"], csv_file)
    else:
        click.echo(click.style("Error: Invalid File Path", bold=True, fg="red"))


@click.command(
    name="delete_user",
    help="Delete users via email address",
)
@click.option(
    "-f",
    "--file",
    "file_name",
    help="path to line-seperated file of user accounts to be deleted",
)
@click.option(
    "-e",
    "--user_email",
    help="Email address of user to be deleted",
)
@click.pass_context
def delete_user(ctx: click.Context, file_name: str = None, user_email: str = None):
    """Delete a user from the Falcon tenant by email address, or delete many using a file."""
    email_list = []
    if file_name is not None:
        try:
            with open(file_name, newline="", encoding="utf-8") as email_list_file:
                email_list = email_list_file.read().splitlines()
            user_deletion(ctx.obj["client"], email_list)
        except FileNotFoundError:
            click.echo(click.style("Error: Invalid File Path", bold=True, fg="red"))
    elif user_email is not None:
        email_list.append(user_email)
        user_deletion(ctx.obj["client"], email_list)
    else:
        click.echo(
            click.style(
                "Please specify either a file or user email. "
                "Try 'falcon users delete_user --help' for help.",
                bold=True,
                fg="red",
            )
        )


@click.command(name="describe_users", help="List all existing users in the cloud instance")
@click.pass_context
def describe_users(ctx: click.Context):
    """Show all the user accounts in the Falcon tenant, and their respective roles."""
    describe_existing_users(ctx.obj["client"])


@click.command(name="list_roles", help="List all available roles in the cloud instance")
@click.pass_context
def list_roles(ctx: click.Context):
    """Show all the roles that exist within the Falcon tenant and may be assigned to users."""
    print_formatted_user_roles(ctx.obj["client"])


@click.command(name="add_roles", help="Add roles via user email and role ID")
@click.pass_context
def add_roles(ctx: click.Context):
    """Grant new roles to a user account in the Falcon tenant."""
    add_roles_to_user(ctx.obj["client"])


cli_users.add_command(add_user)
cli_users.add_command(import_users)
cli_users.add_command(delete_user)
cli_users.add_command(describe_users)
cli_users.add_command(list_roles)
cli_users.add_command(add_roles)
