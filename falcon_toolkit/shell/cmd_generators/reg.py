"""Falcon Toolkit: Shell Generators: Reg.

This file contains a command generator for the reg command, which is particularly complex
to parse in one function.
"""
from argparse import Namespace

from falcon_toolkit.shell.cmd_generators.common import CommandBuilderException


def _reg_delete_builder(args: Namespace) -> str:
    """Build a reg delete command string."""
    if args.value:
        return f'reg delete {args.subkey} {args.value}'

    return f'reg delete {args.subkey}'


def _reg_load_builder(args: Namespace) -> str:
    """Build a reg load command string."""
    if args.troubleshooting:
        return f'reg load {args.filename} {args.subkey} -Troubleshooting'

    return f'reg load {args.filename} {args.subkey}'


def _reg_query_builder(args: Namespace) -> str:
    """Build a reg query command string."""
    if args.value and not args.subkey:
        raise CommandBuilderException("You must specify a value name, type and data together")

    if args.subkey and args.value:
        return f'reg query {args.subkey} {args.value}'

    if args.subkey and not args.value:
        return f'reg query {args.subkey}'

    return 'reg query'


def _reg_set_builder(args: Namespace) -> str:
    """Build a reg set command string."""
    if args.value_name or args.value_type or args.data:
        if args.value_name and args.value_type and args.data:
            return (
                f'reg set {args.subkey} {args.value_name} '
                f'-ValueType={args.value_type} -Value={args.data}'
            )

        raise CommandBuilderException("You must specify a value name, type and data together")

    return f'reg set {args.subkey}'


def _reg_unload_builder(args: Namespace) -> str:
    """Build a reg unload command string."""
    if args.troubleshooting:
        return f'reg unload {args.subkey} -Troubleshooting'

    return f'reg unload {args.subkey}'


def reg_builder(args: Namespace) -> str:
    """Build a reg command based on args passed to do_reg()."""
    if args.command_name == "delete":
        return _reg_delete_builder(args)

    if args.command_name == "load":
        return _reg_load_builder(args)

    if args.command_name == "query":
        return _reg_query_builder(args)

    if args.command_name == "set":
        return _reg_set_builder(args)

    if args.command_name == "unload":
        return _reg_unload_builder(args)

    # This exception should be impossible to reach, as the argument parser should
    # enforce choosing one of the five possible commands
    raise CommandBuilderException("Incorrect mode specified")
