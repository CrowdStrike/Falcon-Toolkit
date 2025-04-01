"""Falcon Toolkit: Shell Utilities.

This file contains helper functions for the main shell.
"""

import json
import os
from typing import Dict, List

import click
import tabulate
from caracara.modules.rtr import GetFile


def _output_complex_falcon_script_result(result: Dict[str, List[Dict[str, str]]]):
    """Output a complex single result table.

    Example of a complex output: InstalledProgram. Each result will look like this:
    {
        "Win32": [
            {
                "Name": "Application Name 1",
                "Version": "1.0.0.0",
                "ProgramId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "Vendor": "Some Vendor"
            },
            {
                "Name": "Application Name 2",
                "Version": "2.0.0.0",
                "ProgramId": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "Vendor": "Some Other Vendor"
            },
            ...
        ],
        "Store": [
            // Another set of dictionaries
        ]
    }
    For this case, we turn each list of dictionaries into a separate table, with the
    outermost key (e.g., Win32, Store) outputted on screen in bold text. Since we don't
    know without inspecting each script's workflow schema (if present) which fields might be
    returned, this function is as generic as possible.
    There is one special case: if a field is called "Name", we always put it first so we can
    alphabetically sort based on it.
    """
    for result_key, result_list in result.items():
        click.echo(click.style(result_key, bold=True))
        key_set = set()
        for result_list_item in result_list:
            for key in result_list_item.keys():
                key_set.add(key)

        # We don't want a None item if one is present.
        if None in key_set:
            key_set.remove(None)

        # Sort all the headers alphabetically, but if there's a Name header it should
        # appear first.
        # Source: https://stackoverflow.com/a/23090686
        headers = sorted(list(key_set), key=lambda x: (x != "Name", x))
        styled_headers = [click.style(header, bold=True) for header in headers]

        # For each inner dictionary, we build a list representing its fields in the order
        # of the headers. Since we're stripping the key away here, order is the only way
        # that tabulate will print the fields in the right order (and, hence, the right
        # cells).
        rows = []
        for inner_result in result_list:
            row = []
            for header in headers:
                # We use .get() as we want None results to be inserted as blank cells
                row.append(inner_result.get(header))
            rows.append(row)

        # Sort all rows by the first column's value. If there is a Name column, this should result
        # in sorting all the records by their Name.
        rows.sort(key=lambda x: x[0])

        # Finally, print this result key's table to screen, before we move on to the next
        # dictionary entry and embedded list.
        click.echo(tabulate.tabulate(rows, headers=styled_headers, tablefmt="fancy_grid"))


def _output_simple_single_falcon_script_result(result: Dict[str, str]):
    r"""Output a single, simple result as a single two column table that maps keys to values.

    This is useful for simpler Falcon scripts like FileInfo that output a single set of properties,
    and allows Falcon Toolkit to display a similar output structure to the Falcon UI.

    Example of a simple output: FileInfo. Each result will look like this:
    {
        "Mode": "-a----",
        "FileName": "C:\\Path\\To\\File.txt",
        "CreationTime": "2025-03-31T00:00:00Z",
        "LastAccessTime": "2025-03-31T00:00:00Z",
        "Group": "HOSTNAME\\None",
        "LastWriteTime": "2025-03-31T00:00:00Z",
        "Sddl": "Long-String-Here",
        "Owner": "HOSTNAME\\username",
        "Length": 1000,
        "Sha256": "eafa198d4e4930337effc7d7eee9c177f063a82f3d6583107b8eeeeed8e18a3d"
    }
    For this case, we can simply tabulate without a header row, where each row contains a cell for
    the key and a cell for the value.
    """
    rows = []
    for result_key, result_value in result.items():
        # Sometimes we just get a list of strings and we can neaten that up
        printable_result_value = result_value
        if isinstance(result_value, list):
            printable_result_value = "\n".join(printable_result_value)
        rows.append(
            [
                click.style(result_key, bold=True),
                printable_result_value,
            ]
        )
    click.echo(tabulate.tabulate(rows, tablefmt="fancy_grid"))


def _output_simple_multi_falcon_script_result(results: List[Dict[str, str]]):
    """Amalgamate many simple results into a single table for easier reading.

    This is useful for simpler Falcon scripts like EventSource, LocalGroup, etc.
    """
    # Build a set of every field in each result to ensure we them all shown.
    key_set = set()
    for result in results:
        for key in result.keys():
            key_set.add(key)

    if None in key_set:
        key_set.remove(None)

    # Sort all the headers alphabetically, but if there's a Name header it should
    # appear first.
    # Source: https://stackoverflow.com/a/23090686
    headers = sorted(list(key_set), key=lambda x: (x != "Name", x))
    styled_headers = [click.style(header, bold=True) for header in headers]

    rows = []
    for result in results:
        row = []
        for header in headers:
            data = result.get(header)

            # Sometimes the data is just a list of strings
            # We break them up using line breaks to make the table work better.
            if data:
                if isinstance(data, list):
                    data = "\n".join(data)

            row.append(data)
        rows.append(row)

    # Sort all rows by the first column's value. If there is a Name column, this should result in
    # sorting all the records by their Name.
    rows.sort(key=lambda x: x[0])

    click.echo(tabulate.tabulate(rows, headers=styled_headers, tablefmt="fancy_grid"))


def output_falcon_script_result(stdout: str) -> bool:
    """Format the output from a Falcon script as a table.

    Falcon scripts accept JSON input and return JSON back. Sometimes this JSON includes nested
    data, so thsi utility function attempts to work through these possible JSON structures and
    format the output appropriately and in a visually useful way.

    The function will return True if it was likely able to print the data to screen correctly;
    otherwise, it'll return False so that it can be printed by the prompt.

    There are broadly two types of outputs from the Falcon scripts:
    - Simple outputs will provide a list of results, where each result is a simple dictionary.
      We can iterate over the dictionary output to transform each result into a neat tabulate
      formatted table.
    - Complex outputs that include nested dictionaries.
    """
    # Attempt to load the JSON response from the Falcon Script
    try:
        json_response = json.loads(stdout)
    except json.decoder.JSONDecodeError:
        click.echo(
            click.style(
                "Could not decode Falcon script response from this system as JSON",
                fg="red",
            )
        )
        return False

    results = json_response.get("result")
    if results is None:
        click.echo(
            click.style(
                "No results returned by the Falcon script from this system",
                fg="yellow",
            )
        )
        return False

    if len(results) == 1:
        click.echo(click.style("1 result:", bold=True))
    else:
        click.echo(click.style(f"{len(results)} results:", bold=True))

    first_result = results[0]
    if len(results) == 1 and isinstance(first_result, dict) and first_result:
        first_result_first_value = list(first_result.values())[0]
        if isinstance(first_result_first_value, list):
            _output_complex_falcon_script_result(first_result)
            return True

    if len(results) == 1:
        # In this simple case, we assume a simple key->value table per result.
        _output_simple_single_falcon_script_result(first_result)
        return True

    # Assume we have multiple results that we want to amalgamate into one big table to avoid
    # repeating many smaller tables of different widths.
    _output_simple_multi_falcon_script_result(results)
    return True


def output_file_name(get_file: GetFile, hostname: str):
    """Create an output filename with the hostname in it."""
    if get_file.filename.startswith("/"):
        # macOS or *nix path
        filename = get_file.filename.rsplit("/", maxsplit=1)[-1]
    else:
        # Windows path
        filename = get_file.filename.rsplit("\\", maxsplit=1)[-1]

    filename_noext, ext = os.path.splitext(filename)

    final_filename = f"{filename_noext}_{hostname}_{get_file.device_id}_{get_file.sha256}{ext}"

    return final_filename
