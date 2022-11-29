"""Falcon Toolkit: Shell Generators.

This file contains ccommon code required by command generators, which are helper functions
 for complex commands that take many lines of code to parse properly.
"""


class CommandBuilderException(Exception):
    """This exeception is raied when a command builder fails to parse the arguments."""
