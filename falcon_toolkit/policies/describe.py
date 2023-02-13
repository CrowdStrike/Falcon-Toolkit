"""Falcon Toolkit: Policy Management.

This code file contains all the logic required to describe policies in a visually clean way.
"""
from textwrap import TextWrapper
from typing import List

import click
import tabulate

from caracara.common.policy_wrapper import (
    MLSliderPolicySetting,
    Policy,
    TogglePolicySetting,
)

from falcon_toolkit.policies.constants import (
    ASCII_OFF_BUTTON,
    ASCII_ON_BUTTON,
)


def pretty_print_policies(policies: List[Policy]):
    """Format a list of Prevention or Detection policies neatly and write them out to screen."""
    for policy in policies:
        click.echo(
            click.style(policy.name, bold=True) +
            " (Platform: " +
            click.style(policy.platform_name, fg='red') +
            ")"
        )
        if policy.description:
            click.echo(f"    {policy.description}")

        # Build up a table containing all the policy settings
        settings_table = []
        # Each setting description will be at most 40 characters wide
        setting_desc_wrap = TextWrapper()
        setting_desc_wrap.width = 40

        for settings_group in policy.settings_groups:
            settings_table.append([click.style(settings_group.name, fg="blue", bold=True)])

            # Each group of settings will have at least one row to itself.
            # Groups of settings with >4 settings will get extra dedicated, contiguous rows.
            row: List[str] = []
            for setting in settings_group.settings:
                # We limit each row to no more than four columns, which matches the Falcon UI
                # whilst also conveniently supporting ML Sliders (which take two cells each)
                if len(row) == 4:
                    settings_table.append(row)
                    row = []

                # Create a list of cells used by each setting to accommodate for settings that
                # need to be split out into separate cells. Right now, we use this functionality
                # for ML sliders so that they can have one cell for Detection, and one for
                # Prevention.
                setting_cells = []

                setting_title = (
                    click.style(setting.name, bold=True) +
                    "\n" +
                    '\n'.join(setting_desc_wrap.wrap(setting.description)) +
                    "\n"
                )
                if isinstance(setting, TogglePolicySetting):
                    # Toggles have an ON or OFF button ASCII graphic available
                    if setting.enabled:
                        setting_cells.append(f"{setting_title}{ASCII_ON_BUTTON}")
                    else:
                        setting_cells.append(f"{setting_title}{ASCII_OFF_BUTTON}")

                elif isinstance(setting, MLSliderPolicySetting):
                    # ML Sliders are split over two cells, and currently only render as text
                    setting_cells.append(f"{setting_title}Detection\n{setting.detection}")
                    setting_cells.append(f"{setting_title}Prevention\n{setting.prevention}")

                # Add all the cells occupied by this setting to the setting group's row
                row.extend(setting_cells)

            # Take a row of settings and append it to the Policy's overall table
            settings_table.append(row)

        # Write the table to screen
        click.echo(tabulate.tabulate(
            settings_table,
            tablefmt="fancy_grid",
        ))

        # Draw some blank space and a divider line to go between Policies
        click.echo()
        click.echo("-"*80)
        click.echo()
