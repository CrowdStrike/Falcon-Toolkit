"""Falcon Toolkit: Host Search.

This functionality allows users to search for hosts without connecting to them.
Once a set of filters has been decided upon, swapping 'host_search' for 'shell' at the CLI will
launch a batch RTR shell with these systems.
"""
import logging
from operator import itemgetter

from textwrap import TextWrapper
from typing import List, Optional

import click
import click_spinner
import tabulate

from caracara import Client
from caracara.filters import FalconFilter


def vertically_align_middle(row_data: List[str]):
    """Align all rows shorter than the tallest row as close to the middle as possible."""
    # Find the tallest row
    tallest_row_height = 0
    for cell in row_data:
        tallest_row_height = max(tallest_row_height, cell.count("\n") + 1, 0)

    if tallest_row_height < 3:
        # We don't bother making any changes if any rows are 1 or 2 high.
        return

    for i, cell in enumerate(row_data):
        new_lines = cell.count("\n")
        if tallest_row_height > new_lines + 1:
            align_line_breaks = max((tallest_row_height + 1) // 2 - 1, 0)
            row_data[i] = '\0' + '\n' * align_line_breaks + cell


def host_search_cmd(
    client: Client,
    filters: FalconFilter,
    online_state: Optional[str],
):
    """Search for hosts that match the provided filters."""
    click.echo(click.style("Searching for hosts...", fg='magenta'))

    fql = filters.get_fql()

    with click_spinner.spinner():
        host_data = client.hosts.describe_devices(filters=fql, online_state=online_state)

    logging.debug(host_data)

    header_row = [
        click.style("Device ID", bold=True, fg='blue'),
        click.style("Hostname", bold=True, fg='blue'),
        click.style("Last Seen", bold=True, fg='blue'),
        click.style("Local IP Address", bold=True, fg='blue'),
        click.style("OS Version", bold=True, fg='blue'),
        click.style("Domain", bold=True, fg='blue'),
        click.style("Containment", bold=True, fg='blue'),
        click.style("Grouping Tags", bold=True, fg='blue'),
    ]
    table_rows = []

    grouping_tag_wrap = TextWrapper()
    grouping_tag_wrap.width = 40

    sixteen_wrap = TextWrapper()
    sixteen_wrap.width = 16

    for aid in host_data.keys():
        hostname = host_data[aid].get("hostname", "<NO HOSTNAME>")

        containment_status = host_data[aid].get('status', 'normal')
        if containment_status == 'normal':
            containment_str = click.style("Not Contained", fg='green')
        elif containment_status == 'contained':
            containment_str = click.style("Contained", fg='red')
        elif containment_status == 'containment_pending':
            containment_str = click.style("Pending", fg='yellow')
        else:
            containment_str = "Unknown"

        grouping_tags = '\n'.join(
            grouping_tag_wrap.wrap(", ".join(host_data[aid].get("tags", "")))
        )

        row = [
            click.style(aid, fg='red'),
            click.style(hostname, bold=True),
            host_data[aid].get('last_seen', '').replace('T', '\n').replace('Z', ''),
            host_data[aid].get('local_ip', ''),
            '\n'.join(sixteen_wrap.wrap(host_data[aid].get('os_version', ''))),
            '\n'.join(sixteen_wrap.wrap(host_data[aid].get('machine_domain', ''))),
            containment_str,
            grouping_tags,
        ]
        table_rows.append(row)

    table_rows = sorted(table_rows, key=itemgetter(1, 0))

    for row in table_rows:
        vertically_align_middle(row)

    table_rows.insert(0, header_row)

    click.echo(tabulate.tabulate(
        table_rows,
        tablefmt='fancy_grid',
    ))
