"""Falcon Toolkit: User Management.

This file contains the logic required to create and configure users.
"""

import csv
import sys
from operator import itemgetter
from textwrap import TextWrapper
from typing import Dict, List, Optional, Set

import click
import click_spinner
import tabulate
from caracara import Client
from caracara.common.csdialog import csradiolist_dialog
from caracara.common.exceptions import GenericAPIError
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter

from falcon_toolkit.hosts import host_search


def _tabulate_users(  # pylint: disable=R0914
    user_data: List[Dict[str, str]] | Dict[str, str],
    role_data: Optional[Dict[str, Dict]] = None,
) -> None:
    """Pretty print a list of users to screen in a tabular format."""
    header_row = [
        click.style("Name", bold=True, fg="blue"),
        click.style("Email Address", bold=True, fg="blue"),
        click.style("Status", bold=True, fg="blue"),
        click.style("Creation Date", bold=True, fg="blue"),
        click.style("Modification Date", bold=True, fg="blue"),
        click.style("UUID", bold=True, fg="blue"),
        click.style("Roles", bold=True, fg="blue"),
    ]
    table_rows = []

    grouping_tag_wrap = TextWrapper()
    grouping_tag_wrap.width = 40

    sixteen_wrap = TextWrapper()
    sixteen_wrap.width = 16

    for extracted_dict in user_data:
        email_address = extracted_dict["uid"]
        name = (
            str(extracted_dict["first_name"])
            + " "
            + str(extracted_dict["last_name"])
        )
        creation_date = extracted_dict["created_at"]
        modification_date = extracted_dict["updated_at"]
        uuid = extracted_dict["uuid"]
        if role_data:
            roles_list = sorted([
                role_data[x]["display_name"] if x in role_data else x
                for x in extracted_dict["roles"]
            ])
        else:
            roles_list = extracted_dict["roles"]

        activation_status = extracted_dict["status"]
        if activation_status == "active":
            status = click.style("Active", fg="green")
        else:
            status = click.style(activation_status, fg="red")

        string_roles = ""
        for role in roles_list:
            string_roles = string_roles + role + "\n"

        row = [name, email_address, status, creation_date, modification_date, uuid, string_roles]
        table_rows.append(row)

    table_rows = sorted(table_rows, key=itemgetter(1, 0))

    for row in table_rows:
        host_search.vertically_align_middle(row)

    table_rows.insert(0, header_row)

    click.echo(
        tabulate.tabulate(
            table_rows,
            tablefmt="fancy_grid",
        )
    )


def add_csv_users(client: Client, csv_name: str):  # pylint: disable=R0914
    """Create users based on a CSV formatted first_name,last_name,email_address."""
    successful_uuid_set: Set[str] = set()

    with open(csv_name, newline="", encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        if (
            "first_name" not in reader.fieldnames or
            "last_name" not in reader.fieldnames or
            "email_address" not in reader.fieldnames
        ):
            raise KeyError(
                "The CSV must contain at least the fields first_name, last_name, and email_address"
            )

        for row in reader:
            first_name = row["first_name"]
            last_name = row["last_name"]
            email_address = row["email_address"]
            uuid: Optional[str] = None

            click.echo(
                "Processing user: " +
                click.style(f"{first_name} {last_name}", bold=True) +
                " (" +
                click.style(email_address, bold=True) +
                ")"
            )

            try:
                user_add_result = client.users.add_user(
                    first_name,
                    last_name,
                    email_address,
                )
                uuid = user_add_result["uuid"]
                successful_uuid_set.add(uuid)

            except GenericAPIError as bad_user_error:
                print(click.style(bad_user_error, bold=True, fg="yellow"))
            except KeyError:
                print(click.style("The API response did not include a new user UUID", fg="red"))

            if "roles" in row and row["roles"] is not None:
                roles_str = row["roles"]
                click.echo(f"Adding roles to user {email_address}: {roles_str}")

                if not uuid:
                    uuid = client.users.get_uuid_by_email(email_address)

                roles = roles_str.split(",")
                if client.users.add_user_roles(uuid, roles):
                    successful_uuid_set.add(uuid)
                else:
                    print(click.style(f"Role addition failed for {roles}", bold=True, fg="red"))

    if not successful_uuid_set:
        # Nothing succeeded
        return

    with click_spinner.spinner():
        user_data = client.users.describe_users(user_uuids=list(successful_uuid_set))
        role_data = client.users.describe_available_roles()

    click.echo(click.style("Affected Users", bold=True))
    _tabulate_users(list(user_data.values()), role_data)


def add_single_user(
    client: Client, first_name: str, last_name: str, email_address: str
):
    """Create a single user in the Falcon tenant."""
    with click_spinner.spinner():
        result = client.users.add_user(first_name, last_name, email_address)
        user_data = client.users.describe_users(user_uuids=[result["uuid"]])

    click.echo(click.style("New User", bold=True))
    _tabulate_users(list(user_data.values()))


def delete_user_guardrails(email_addresses: list):
    """Confirm via a visual Prompt Toolkit box whether the user really wants to delete a user."""
    confirmation_options = [
        (False, "Abort"),
        (True, "Delete accounts"),
    ]
    prompt_text = (
        "Are you sure you want to delete these accounts? \n" +
        "\n".join(email_addresses)
    )
    confirmation: bool = csradiolist_dialog(
        title="Confirm User Deletion Action",
        text=prompt_text,
        values=confirmation_options,
    ).run()

    if confirmation:
        click.echo(click.style("User confirmed action", bold=True, fg="green"))
        return True

    click.echo(click.style("Aborted!", bold=True, fg="red"))
    return False


def user_deletion(client: Client, email_addresses: list):
    """Validate email addresses, confirm deletion, and ultimately delete users."""
    uuid_list = []
    bad_emails = []
    for i in email_addresses:
        try:
            uuid = client.users.get_uuid_by_email(i)
            uuid_list.append(uuid)
        except GenericAPIError:
            click.echo(click.style(f"Invalid Email Address: {i}", bold=True, fg="red"))
            bad_emails.append(i)

    good_emails = [email for email in email_addresses if email not in bad_emails]
    if good_emails and delete_user_guardrails(good_emails):
        for i in uuid_list:
            deletion_result = client.users.delete_user(i)
            if deletion_result is False:
                click.echo(click.style(f"Error deleting user: {i}", bold=True, fg="red"))


def print_formatted_user_roles(client: Client):
    """Retrieve all available user roles, and format them on screen."""
    unformatted_roles = client.users.describe_available_roles()
    for role_key in unformatted_roles:
        all_values = unformatted_roles[role_key]
        user_id = all_values["id"]
        display_name = all_values["display_name"]
        description = all_values["description"]
        is_global = all_values["is_global"]
        print(click.style(f"ID: {user_id}", bold=True, fg="green"))
        print(f"Display Name: {display_name}")
        print(f"Is Global: {is_global}")
        print("Description:")
        print(description)
        print("")


def add_roles_to_user(client: Client):
    """Autocomplete role names to efficiently add roles to a user via email address.

    Sensor Download READ permissions required.
    """
    try:
        user_email = prompt("Enter the user email address: ")
        user_uuid = client.users.get_uuid_by_email(user_email)
    except GenericAPIError as error:
        print(click.style(error, bold=True, fg="red"))
        sys.exit()

    selected_roles = []
    all_roles = []
    all_roles_meta_dict = {}

    unformatted_roles = client.users.describe_available_roles()
    for role_key in unformatted_roles:
        all_values = unformatted_roles[role_key]
        all_roles.append(all_values["id"])
        all_roles_meta_dict[all_values["id"]] = all_values["display_name"]

    list_completer = FuzzyWordCompleter(
        all_roles,
        meta_dict=all_roles_meta_dict,
    )
    add_more_roles = "yes"
    while add_more_roles.lower() == "yes" or add_more_roles.lower() == "y":
        role_option = prompt("Select Role: ", completer=list_completer)
        selected_roles.append(role_option)
        add_more_roles = prompt("Add more roles? (yes or no): ")

    print(f"Adding selected roles: {selected_roles}")
    actually_add = prompt("Continue? (yes or no): ")
    if (
        actually_add.lower() == "yes"
        or actually_add.lower() == "y"
    ):

        result = client.users.add_user_roles(user_uuid, selected_roles)
        if result is True:
            print(click.style("Successfully added roles", bold=True, fg="green"))
        else:
            print(click.style("Operation Failed, Check Role Name", bold=True, fg="red"))
    else:
        print("Cancelling operation")


def describe_existing_users(client: Client):
    """Show all users in a CID within a formatted table."""
    with click_spinner.spinner():
        user_data = client.users.describe_users()
        role_data = client.users.describe_available_roles()
        formatted_data = list(user_data.values())

    _tabulate_users(formatted_data, role_data)
