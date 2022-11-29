"""Falcon Toolkit: Shell.

This file contains parsers that allow for tab completion, help, and appropriate argument storage for
each command. Each command that exists in RTR within the Cloud must be implemented here for the
shell to expose it to a user.
"""
import functools
import os

from cmd2 import (
    Cmd,
    Cmd2ArgumentParser,
)
from falcon_toolkit.common.namespace import FalconRecursiveNamespace

CLOUD_SCRIPT_CHOICES = []
PUT_FILE_CHOICES = []

# For all commands that take no arguments at all,
# we can reuse this blank argparser to avoid instantiating
# lots of empty/blank argparsers objects
blank_argparser = Cmd2ArgumentParser()

cat_argparser = Cmd2ArgumentParser()
cat_argparser.add_argument(
    'file',
    help="File to read the contents of",
)

cat_argparser.add_argument(
    '-b',
    '--ShowHex',
    help='Show the results in hexadecimal byte format instead of ASCII',
    dest='show_hex',
    action='store_true',
)

cd_argparser = Cmd2ArgumentParser()
cd_argparser.add_argument(
    'directory',
    help="Directory to change to",
)

cloud_scripts_argparser = Cmd2ArgumentParser()
cloud_scripts_argparser.add_argument(
    '-s',
    '--show-content',
    help=(
        "Show the content of each script on-screen "
        "(may produce long outputs!)"
    ),
    dest='show_content',
    action='store_true',
)
cloud_scripts_argparser.add_argument(
    'script_name',
    help=(
        "Only show information about a specific script "
        "(default: all scripts)"
    ),
    nargs='?',
    choices=CLOUD_SCRIPT_CHOICES,
)

cp_argparser = Cmd2ArgumentParser()
cp_argparser.add_argument(
    'source',
    help="Source File or Directory",
)
cp_argparser.add_argument(
    'destination',
    help="Destination File or Directory",
)

download_argparser = Cmd2ArgumentParser()
download_dir_completer = functools.partial(
    Cmd.path_complete,
    path_filter=lambda path: os.path.isdir(path),  # pylint: disable=unnecessary-lambda
)
download_argparser.add_argument(
    'destination',
    help="Destination directory on the local system to download files to",
    completer=download_dir_completer,
)
download_argparser.add_argument(
    '-b',
    '--batch-get-req-id',
    help="Batch request ID (defaults to the most recent get command)",
    dest='batch_get_req_id',
    type=str,
    nargs='?',
)
download_argparser.add_argument(
    '-e',
    '--extract',
    help="Extract and delete the downloaded 7z archive, leaving only the retrieved file itself",
    action='store_true',
    dest='extract_7z',
)

eventlog_argparser = Cmd2ArgumentParser()
eventlog_subparsers: Cmd2ArgumentParser = eventlog_argparser.add_subparsers(
    title='Commands',
    description='Inspect event logs',
    dest="command_name",
    required=True,
)
eventlog_parser_backup: Cmd2ArgumentParser = eventlog_subparsers.add_parser(
    "backup",
    help="Back up the specified event log to a file (.evtx) on disk",
)
eventlog_parser_backup.add_argument(
    "name",
    help="Name of the event log to back up (e.g. Application, System)",
)
eventlog_parser_backup.add_argument(
    "filename",
    help="Target file on disk",
)
eventlog_parser_export: Cmd2ArgumentParser = eventlog_subparsers.add_parser(
    "export",
    help="Export the specified event log to a file (.csv) on disk",
)
eventlog_parser_export.add_argument(
    "name",
    help="Name of the event log to back up (e.g. Application, System)",
)
eventlog_parser_export.add_argument(
    "filename",
    help="Target file on disk",
)
eventlog_parser_list: Cmd2ArgumentParser = eventlog_subparsers.add_parser(
    "list",
    help="Event log list: show available event log sources",
)
eventlog_parser_view: Cmd2ArgumentParser = eventlog_subparsers.add_parser(
    "view",
    help="View most recent N events in a given event log",
)
eventlog_parser_view.add_argument(
    "name",
    help="Name of the event log to view (e.g. Application, System)",
)
eventlog_parser_view.add_argument(
    "count",
    type=int,
    nargs='?',
    help="Number of entries to return. Default: 100; Maximum: 500",
)
eventlog_parser_view.add_argument(
    "source_name",
    nargs='?',
    help="Name of the event source, e.g. 'WinLogon'"
)
ls_argparser = Cmd2ArgumentParser()
ls_argparser.add_argument(
    'directory',
    default='.',
    nargs='?',
    help="Directory to list",
)
ls_argparser.add_argument(
    '-l',
    '--long',
    help="[Linux] List in long format",
    action='store_true',
    dest='long_format',
)
ls_argparser.add_argument(
    '-L',
    '--follow-symlinks',
    help=(
        "[Linux] Follow all symbolic links to final target and "
        "list the file or directory the link references, "
        "rather than the link itself"
    ),
    action='store_true',
    dest='follow_symlinks',
)
ls_argparser.add_argument(
    '-R',
    '--recurse',
    help="[Linux] Recursively list subdirectories encountered",
    action='store_true',
    dest='recursive',
)
ls_argparser.add_argument(
    '-T',
    '--time-modified',
    help=(
        "[Linux] Sort by time modified (most recently modified first), "
        "before sorting the operands by lexicographical order"
    ),
    action='store_true',
    dest='sort_time_modified',
)

encrypt_argparser = Cmd2ArgumentParser()
encrypt_argparser.add_argument(
    'path',
    help="File to encrypt",
)
encrypt_argparser.add_argument(
    'key',
    nargs='?',
    help='Base64 encoded encryption key (optional)',
)

env_argparser = Cmd2ArgumentParser()

filehash_argparser = Cmd2ArgumentParser()
filehash_argparser.add_argument(
    'file',
    help="File to calculate hashes for",
)

get_argparser = Cmd2ArgumentParser()
get_argparser.add_argument(
    'file',
    help="Path to file to be uploaded to the CrowdStrike cloud",
)

get_status_argparser = Cmd2ArgumentParser()
get_status_argparser.add_argument(
    'batch_get_req_id',
    nargs='?',
    help='ID of batch request to get. Defaults to the last batch request.',
)

kill_argparser = Cmd2ArgumentParser()
kill_argparser.add_argument(
    'pid', help="Process ID"
)

map_argparser = Cmd2ArgumentParser()
map_argparser.add_argument(
    'drive_letter',
    help="Drive letter (with or without ':')",
)
map_argparser.add_argument(
    'network_share',
    help='UNC path of remote share',
)
map_argparser.add_argument(
    'username',
    help='User account used for the connection',
)
map_argparser.add_argument(
    'password',
    help='Password for the user account',
)

memdump_argparser = Cmd2ArgumentParser()
memdump_argparser.add_argument(
    'pid',
    help=(
        'PID (Process ID) of the process. '
        'Use the "ps" command to discover possible values'
    ),
)
memdump_argparser.add_argument(
    'filename',
    help='Absolute or relative path for dump output file',
)

mkdir_argparser = Cmd2ArgumentParser()
mkdir_argparser.add_argument(
    'directory',
    help="Name of new directory to create",
)

mount_argparser = Cmd2ArgumentParser()
mount_subparsers = mount_argparser.add_subparsers(
    title='[Linux/macOS] Mount a filesystem',
    description='Mount a filesystem on Linux or macOS. The Windows equivalent is the map command',
    required=False,
)
mount_macos_subparser = mount_subparsers.add_parser(
    'source', help='Source filesystem, possibly a URL including username and password',
)
mount_macos_subparser.add_argument(
    'mount_point',
    help='Path to the desired mount point',
)
mount_macos_subparser.add_argument(
    '-t',
    required=False,
    dest='filesystem_type',
    help='Filesystem type (e.g., nfs, smbfs)',
    nargs=1,
)
mount_macos_subparser.add_argument(
    '-o',
    required=False,
    dest='mount_options',
    help='Mount options (e.g., nobrowse)',
    nargs=1,
)

mv_argparser = Cmd2ArgumentParser()
mv_argparser.add_argument(
    'source',
    help='Source file or directory. Absolute or relative path.',
)
mv_argparser.add_argument(
    'destination',
    help='Destination. Absolute or relative path.',
)

netstat_argparser = Cmd2ArgumentParser()
netstat_argparser.add_argument(
    '-nr',
    help='Show routing information',
    dest='routing_info',
    action='store_true',
)

put_argparser = Cmd2ArgumentParser()
put_argparser.add_argument(
    'file',
    help='Name of the file to download to the host from the CrowdStrike Cloud',
    choices=PUT_FILE_CHOICES,
)

put_and_run_argparser = Cmd2ArgumentParser()
put_and_run_argparser.add_argument(
    'file',
    help=(
        '[Windows] Name of the file to download to the host from the CrowdStrike Cloud, '
        'and consequently execute. The file will be executed from the directory: '
        'C:\\windows\\system32\\drivers\\crowdstrike\\rtr\\putrun.'
    ),
    choices=PUT_FILE_CHOICES,
)

reg_argparser = Cmd2ArgumentParser()
reg_subparsers: Cmd2ArgumentParser = reg_argparser.add_subparsers(
    title='Registry Inspection and Manipulation',
    description='Choose how to inspect or manipulate the registry',
    dest='command_name',
    required=True,
)
reg_delete_parser: Cmd2ArgumentParser = reg_subparsers.add_parser(
    'delete',
    help='Delete registry subkeys, keys or values',
)
reg_delete_parser.add_argument(
    'subkey',
    help='Registry subkey full path',
)
reg_delete_parser.add_argument(
    'value',
    help='If provided, delete only this value',
    nargs='?',
)
reg_load_parser: Cmd2ArgumentParser = reg_subparsers.add_parser(
    'load',
    help='Load a user registry hive from disk',
)
reg_load_parser.add_argument(
    'filename',
    help='Path to user registry hive (e.g. "C:\\Users\\paul\\NTUSER.DAT")',
)
reg_load_parser.add_argument(
    'subkey',
    help='Registry subkey destination (e.g. "HKEY_USERS\\paul-temp")',
)
reg_load_parser.add_argument(
    '-Troubleshooting',
    dest='troubleshooting',
    help='Flag to print verbose error messages for escalation to support',
    action='store_true',
)
reg_query_parser: Cmd2ArgumentParser = reg_subparsers.add_parser(
    'query',
    help='Query a registry subkey or value',
)
reg_query_parser.add_argument(
    'subkey',
    help='Registry subkey full path',
)
reg_query_parser.add_argument(
    'value',
    nargs='?',
    help='Name of value to query (requires a subkey argument)',
)
reg_set_parser: Cmd2ArgumentParser = reg_subparsers.add_parser(
    'set',
    help='Set registry keys or values. NB: syntax differs from Falcon UI.',
)
reg_set_parser.add_argument(
    'subkey',
    help='Registry subkey full path',
)
reg_set_parser.add_argument(
    "-Value",
    dest='value_name',
    help='Name of value to set',
)
reg_set_parser.add_argument(
    '-ValueType',
    dest='value_type',
    help='Type of value',
    choices=['REG_SZ', 'REG_DWORD', 'REG_QWORD', 'REG_MULTI_SZ', 'REG_BINARY'],
    type=str.upper,
)
reg_set_parser.add_argument(
    '-ValueData',
    dest='data',
    help='Contents of value to insert into Registry',
)
reg_unload_parser: Cmd2ArgumentParser = reg_subparsers.add_parser(
    'unload',
    help='Unload a previously loaded user registry hive',
)
reg_unload_parser.add_argument(
    'subkey',
    help='Registry subkey to unload (e.g. "HKEY_USERS\\paul-temp")',
)
reg_unload_parser.add_argument(
    '-Troubleshooting',
    dest='troubleshooting',
    help='Flag to print verbose error messages for escalation to support',
    action='store_true',
)

restart_argparser = Cmd2ArgumentParser()
restart_argparser.add_argument(
    '-Confirm',
    dest='confirm',
    help='Confirms restart is ok',
    action='store_true',
)

rm_argparser = Cmd2ArgumentParser()
rm_argparser.add_argument(
    'path',
    help='File or directory to delete',
)
rm_argparser.add_argument(
    '-Force',
    dest='force',
    help='Flag to allow directory and recursive deletes',
    action='store_true',
)

run_argparser = Cmd2ArgumentParser()
run_argparser.add_argument(
    "executable",
    help='The absolute path to the executable',
)
run_argparser.add_argument(
    '-CommandLine',
    dest='command_line_args',
    help='Command line arguments passed to the executable',
)
run_argparser.add_argument(
    '-Wait',
    dest='wait',
    help=(
        'Run the program and wait for the result code. '
        'The default behaviour (i.e. without the -Wait option) '
        'is to start the program and return without waiting for '
        'the result code.'
    ),
    action='store_true',
)

runscript_argparser = Cmd2ArgumentParser()
runscript_group = runscript_argparser.add_mutually_exclusive_group(required=True)
runscript_group.add_argument(
    "-CloudFile",
    dest="cloud_file",
    help="Script name in the Falcon dashboard",
    choices=CLOUD_SCRIPT_CHOICES,
)
runscript_group.add_argument(
    "-HostPath",
    dest="host_path",
    help="Absolute or relative path of script on host machine",
)
runscript_group.add_argument(
    "-Raw",
    dest="raw_script",
    help="Run raw script (provided as a parameter)",
)
runscript_group.add_argument(
    "-WorkstationPath",
    dest="workstation_path",
    help=(
        "Run script from a path on the local workstation. "
        "Note that this command does not exist on RTR in the browser."
    ),
    completer=Cmd.path_complete,
)
runscript_argparser.add_argument(
    "-CommandLine",
    dest="command_line_args",
    help="Command line arguments",
    nargs='?',
)
runscript_argparser.add_argument(
    "-Timeout",
    dest="script_timeout",
    help="Set timeout for the script (default: 30s)",
    nargs='?',
    default=30,
    type=int,
)

shutdown_argparser = Cmd2ArgumentParser()
shutdown_argparser.add_argument(
    '-Confirm',
    dest='confirm',
    help='Confirms shutdown is ok',
    action='store_true',
)

tar_argparser = Cmd2ArgumentParser()
tar_argparser.add_argument(
    "source",
    help="Source to compress",
)
tar_argparser.add_argument(
    '-f',
    '--filename',
    help="Target tar filename. Relative or absolute.",
    nargs=1,
    dest='filename',
)
tar_create_update_argparser = tar_argparser.add_mutually_exclusive_group(required=True)
tar_create_update_argparser.add_argument(
    '-c',
    '--create',
    help="Create a new archive, and overwrite any other with the same name",
    dest='create',
    action='store_true',
)
tar_create_update_argparser.add_argument(
    '-u',
    '--update',
    help=(
        "Update an existing archive if one already exists, "
        "otherwise create a new archive (same as -c)"
    ),
    dest='update',
    action='store_true',
)
tar_compression_argparser = tar_argparser.add_mutually_exclusive_group(required=False)
tar_compression_argparser.add_argument(
    '-a',
    '--auto',
    help="Automatically decide on a compression method",
    dest='compress_auto',
    action='store_true',
)
tar_compression_argparser.add_argument(
    '-z',
    '--gzip',
    help="Gzip Compression",
    dest='gzip',
    action='store_true',
)
tar_compression_argparser.add_argument(
    '-j',
    '--bzip2',
    help="Bzip2 Compression",
    dest='bzip2',
    action='store_true',
)
tar_compression_argparser.add_argument(
    '-J',
    '--lzma',
    help="LZMA/XZ Compression",
    dest='lzma',
    action='store_true',
)

umount_argparser = Cmd2ArgumentParser()
umount_argparser.add_argument(
    'filesystem', help='Filesystem to unmount',
)
umount_argparser.add_argument(
    '-f',
    '--force',
    dest='force_umount',
    action='store_true',
)

unmap_argparser = Cmd2ArgumentParser()
unmap_argparser.add_argument(
    'drive_letter',
    help="Drive letter (with or without ':')",
)

update_argparser = Cmd2ArgumentParser()
update_subparsers: Cmd2ArgumentParser = update_argparser.add_subparsers(
    title='Windows Update manipulation',
    description='Choose how to work with Windows Update',
    dest='command_name',
    required=True,
)
update_subparsers.add_parser(
    'history',
    help='Use the Windows Update Agent to list update history',
)
update_install_subparser: Cmd2ArgumentParser = update_subparsers.add_parser(
    'install',
    help=(
        'Use the Windows Update Agent to download and install '
        'the available update matching the input'
    )
)
update_install_subparser.add_argument(
    'kb',
    help=(
        'A string containing one or more KB values. To install one KB, '
        'just provide the number, e.g. update install 4565351. To install '
        'multiple KBs, provide them delimited by spaces surrounded by double '
        'quotes, e.g. update install "4565351 4569751".'
    ),
)
update_subparsers.add_parser(
    'list',
    help='Use the Windows Update Agent to list available updates',
)
update_query_subparser: Cmd2ArgumentParser = update_subparsers.add_parser(
    'query',
    help=(
        'Use the Windows Update Agent to list available updates matching '
        'one or more KBs provided as an input'
    ),
)
update_query_subparser.add_argument(
    'kb',
    help=(
        'A string containing one or more KB values. To query one KB, '
        'just provide the number, e.g. update query 4565351. To query '
        'multiple KBs, provide them delimited by spaces surrounded by double '
        'quotes, e.g. update query "4565351 4569751".'
    ),
)

xmemdump_argparser = Cmd2ArgumentParser()
xmemdump_argparser.add_argument(
    "mode",
    choices=['complete', 'kerneldbg'],
    type=str.lower,
    help=(
        'Complete (complete host memory) or '
        'KernelDbg (kernel memory with debug symbols)'
    ),
)
xmemdump_argparser.add_argument(
    'destination',
    help='Target memdump file name. Absolute or relative path.',
)

zip_argparser = Cmd2ArgumentParser()
zip_argparser.add_argument(
    'source',
    help='Source file or directory',
)
zip_argparser.add_argument(
    'destination',
    help='Target zip file name. Relative or absolute path.',
)

_PARSERS = {
    "cat": cat_argparser,
    "cd": cd_argparser,
    "cloud_scripts": cloud_scripts_argparser,
    "cp": cp_argparser,
    "csrutil": blank_argparser,
    "cswindiag": blank_argparser,
    "download": download_argparser,
    "encrypt": encrypt_argparser,
    "env": env_argparser,
    "eventlog": eventlog_argparser,
    "ls": ls_argparser,
    "filehash": filehash_argparser,
    "get": get_argparser,
    "get_status": get_status_argparser,
    "getsid": blank_argparser,
    "ifconfig": blank_argparser,
    "ipconfig": blank_argparser,
    "kill": kill_argparser,
    "map": map_argparser,
    "memdump": memdump_argparser,
    "mkdir": mkdir_argparser,
    "mount": mount_argparser,
    "mv": mv_argparser,
    "netstat": netstat_argparser,
    "ps": blank_argparser,
    "put": put_argparser,
    "put_and_run": put_and_run_argparser,
    "put_files": blank_argparser,
    "reg": reg_argparser,
    "restart": restart_argparser,
    "rm": rm_argparser,
    "run": run_argparser,
    "runscript": runscript_argparser,
    "shutdown": shutdown_argparser,
    "tar": tar_argparser,
    "umount": umount_argparser,
    "unmap": unmap_argparser,
    "update": update_argparser,
    "xmemdump": xmemdump_argparser,
    "zip": zip_argparser,
}
PARSERS = FalconRecursiveNamespace(**_PARSERS)
