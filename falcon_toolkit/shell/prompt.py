"""Falcon Toolkit: Shell.

This file contains the bulk of the code that implements the RTR batch shell. It is configured, and
in turn instantiated and invoked, by the code within shell/cli.py.
"""
import concurrent.futures
import csv
import os
import sys

from typing import List, Tuple, Optional

import click
import click_spinner

from caracara import Client
from caracara.modules.rtr import (
    BatchGetCmdRequest,
    GetFile,
)
from cmd2 import (
    Cmd,
    Settable,
    with_argparser,
)
from colorama import Fore, Style

from falcon_toolkit.common.console_utils import build_file_hyperlink
from falcon_toolkit.shell.cmd_generators.common import CommandBuilderException
from falcon_toolkit.shell.cmd_generators.reg import reg_builder
from falcon_toolkit.shell.parsers import (
    CLOUD_SCRIPT_CHOICES,
    PARSERS,
    PUT_FILE_CHOICES,
)
from falcon_toolkit.shell.refresh import SessionRefreshTimer
from falcon_toolkit.shell.utils import output_file_name


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class RTRPrompt(Cmd):
    """Implement a Cmd2 REPL that provides batch RTR functionality."""

    last_batch_get_id = None
    last_batch_get_completed_uploads = 0
    last_batch_get_successful_requests = 0

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    def __init__(
        self,
        client: Client,
        device_ids: List[str],
        csv_output_file: str,
        startup_script: str = None,
        timeout: int = 30,
        queueing: bool = False,
    ):
        """Initialise the RTR Prompt.

        This is deliberately a long function, as it does a mixture of device connections,
        internal configuration of the Cmd2 object and adds all necessary hooks to ensure that
        our user-editable parameters ("settables") function, the parsers are set up with the right
        data, and that the shell will be ready to go by the end of the __init__.
        Rough order of __init__ proceedings:
        - Initialise the Cmd2 Cmd object that this prompt is based on
        - Configure scripting by switching on the Python bridge and self inspection
        - Store a Caracara client and list of connected devices into the object for later use
        - Configure settables (e.g., queuing enablement and timeout in seconds)
        - Parallel load data needed for tab completion, as well as device data (so we'll have more
        than just each device's ID, such as its name and OS platform)
        - Configure the post-loop hook to kill off any latent threads before gracefully exiting
        - Derive the most sensible root path, which in turn will configure the prompt appropriately
        - Configure the command output CSV
        - Switch on the session refresh timer
        - Welcome the user to the batch shell
        """
        # Configure the underlying Cmd2 object
        super().__init__(
            allow_cli_args=False,
            startup_script=startup_script,
            include_py=True,
        )

        # This allows inline Python scripts to execute commands on the shell by calling rtr(cmd)
        self.py_bridge_name = "rtr"
        # Expose the RTRPrompt object to inline Python scripts for introspection of state
        self.self_in_py = True

        # Store the Caracara client within the RTRPrompt for usage later
        self.client = client

        # Store the list of devices to be connected to within the RTRPrompt
        self.device_ids = device_ids

        # Initialise this state variable to empty to satisfy linters and protect against code errors
        self.last_batch_get_cmd_req_ids: Optional[List[str]] = None

        # Configure whether RTR queueing should be enabled, and make this user settable via command
        self.queueing = queueing
        self.add_settable(
            Settable(
                'queueing',
                bool,
                "RTR Command Queueing (True or False)",
                self,
                onchange_cb=self._onchange_queueing,
            )
        )

        # Configure the timeout in seconds, and make this user settable via command
        self.timeout = timeout
        self.add_settable(
            Settable(
                'timeout',
                int,
                "RTR Command Timeout (seconds)",
                self,
                onchange_cb=self._onchange_timeout,
            )
        )

        # Load data required for internal tab completion in parallel for maximal performance
        click.echo(click.style("Loading data..."))
        spinner = click_spinner.Spinner()
        spinner.start()

        def _grab_put_files():
            """Load a list of RTR PUT files into the put command's parser.

            This is for tab completion.
            """
            put_files = self.client.rtr.describe_put_files()
            put_file_names = []
            for put_file_id in put_files.keys():
                put_file_names.append(put_files[put_file_id]['name'])
            PUT_FILE_CHOICES.clear()
            PUT_FILE_CHOICES.extend(sorted(put_file_names))

        def _grab_custom_scripts():
            """Load a list of RTR cloud scripts into the runscript command's parser.

            This is for tab completion.
            """
            custom_scripts = self.client.rtr.describe_scripts()
            script_names = []
            for script_id in custom_scripts.keys():
                script_names.append(custom_scripts[script_id]['name'])
            CLOUD_SCRIPT_CHOICES.clear()
            CLOUD_SCRIPT_CHOICES.extend(sorted(script_names))

        # Parallelise all data retrieval tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            grab_put_files_future = executor.submit(_grab_put_files)
            grab_scripts_future = executor.submit(_grab_custom_scripts)
            device_data_future = executor.submit(
                self.client.hosts.get_device_data,
                device_ids,
            )

            _ = grab_put_files_future.result()
            _ = grab_scripts_future.result()
            self.device_data = device_data_future.result()

        spinner.stop()

        click.echo("Connecting to systems")
        self.batch_session = client.rtr.batch_session()
        with click_spinner.spinner():
            self.batch_session.connect(
                device_ids=self.device_ids,
                queueing=self.queueing,
                timeout=self.timeout,
            )

        # Load device data from within each inner batch session into a big dictionary for later use
        self.connected_devices = {}
        for inner_batch_session in self.batch_session.batch_sessions:
            self.connected_devices.update(inner_batch_session.devices)

        # Ensure that the _cleanup function runs when the REPL ends (i.e., via the quit command)
        self.register_postloop_hook(self._cleanup)

        # Identify how many systems actually connected properly based on the 'complete' result
        self.successful_device_connections = sum(
            ('complete' in x and x['complete'] is True) or
            ('offline_queued' in x and x['offline_queued'] is True)
            for x in self.connected_devices.values()
        )

        # Bail out if no devices connected, since this shell will be useless
        if self.successful_device_connections == 0:
            click.echo(click.style(
                "No devices connected successfully. "
                "If this is unexpected, please check the log file.",
                fg="red",
                bold=True,
            ))
            sys.exit(1)

        # Figure out whether the prompt should show a *nix/macOS or Windows prompt, and set this up
        root_path = self._derive_root_path()
        self._set_prompt(root_path)

        # Set up the CSV command output, and configure a DictWriter for later usage
        self.csv_output_file = csv_output_file

        # pylint: disable=consider-using-with
        self.csv_file_handle = open(csv_output_file, 'w', newline='', encoding='utf-8')
        fieldnames = [
            'n',
            'command',
            'aid',
            'hostname',
            'complete',
            'stdout',
            'stderr',
        ]
        self.csv_writer = csv.DictWriter(
            self.csv_file_handle,
            fieldnames=fieldnames,
        )
        self.csv_writer.writeheader()

        # This is effectively a command counter, so that sorting the CSV output can guarantee an
        # order of proceedings where this data is required by users
        self.output_line_n = 1

        # Check every minute whether the RTR session needs refreshing
        self.session_refresh_timer = SessionRefreshTimer(
            60,
            self.batch_session,
            self.timeout,
        )

    intro = (
        "Welcome to the RTR Shell. Type 'help' or '?' to list the available commands.\n"
        "The first host in each response will have its output written to screen. "
        "All hosts will have their outputs written to CSV.\n"
    )
    prompt = "initialising..."

    def _derive_root_path(self) -> str:
        r"""Derive the root path to be used for the REPL prompt.

        This function analyses the list of connected devices and derives a best guess at
        whether to set the prompt to C:\ or /.
        """
        first_queued_root_path = None
        for device in self.connected_devices.values():
            if device['offline_queued']:
                # Queued (offline) hosts will not give us a prompt in stdout
                # Skip, and hope that another host is online
                if not first_queued_root_path:
                    first_queued_root_path = "/"
                    device_id = device['aid']
                    if self.device_data[device_id]['platform_name'] == 'Windows':
                        first_queued_root_path = "C:\\"
                continue

            if 'base_command' in device and device['base_command'] == 'pwd':
                # On initial connection, the pwd pseudo-command will be run
                # to reset the path back to the root and echo it to stdout
                stdout = device['stdout']
                return stdout

            # Something weird has happened in this case, so just return an OS-dependant root
            self.perror(
                Fore.RED + "A connected device does not have a base_command == pwd" + Fore.RESET
            )

        if first_queued_root_path:
            return first_queued_root_path

        # If none of the devices have given us a useful value, just return an OS-dependent root path
        # The iteration trick avoids iterating over the whole dictionary again
        first_device = next(iter(self.connected_devices.items()))[1]
        first_device_id = first_device['aid']
        if self.device_data[first_device_id]['platform_name'] == "Windows":
            return "C:\\"

        # If all else fails, just return a *nix /
        return "/"

    def _set_prompt(self, prompt: str):
        """Set the prompt to a command-line style prompt, corrected based on the likely platform."""
        prompt_character = ">" if ":\\" in prompt else " #"
        self.prompt = f'{Style.DIM}{Fore.WHITE}{prompt}{prompt_character} {Style.RESET_ALL}'

    def _onchange_timeout(self, param_name, old, new):
        """Handle when the timeout parameter is changed."""
        self.session_refresh_timer.timeout = new
        self.poutput(f"Changed RTR command timeout from {old}s to {new}s")

    def _onchange_queueing(self, param_name, old, new):
        """Handle when the queueing parameter is changed.

        If queueing is switched on or off, a full set of reconnections to a fresh set of
        underlying RTR sessions is required.
        """
        if old == new:
            self.poutput(f"Queuing was already set to {old}, so RTR session will not reconnect")
        else:
            self.queueing = new
            self.batch_session.connect(
                device_ids=self.device_ids,
                queueing=self.queueing,
                timeout=self.timeout
            )
            root_path = self._derive_root_path()
            self._set_prompt(root_path)

    def _cleanup(self) -> None:
        """Clean up threads and file handles before the shell exits gracefully."""
        self.poutput("Exiting shell...")

        # Kill the session refresh thread
        self.session_refresh_timer.stop()

        # Fully close the CSV file
        self.csv_file_handle.close()

        # Print a clickable file path to screen allowing users to jump straight to the CSV output
        hyperlink = build_file_hyperlink(self.csv_output_file, self.csv_output_file)
        self.poutput(f"{Fore.GREEN}Log file located at: {hyperlink}")

    def _search_get_files(
        self,
        batch_get_cmd_req_ids: List[str],
    ) -> Optional[List[Tuple[GetFile, str]]]:
        """Search for batch GET files and update the internal device data cache as needed.

        This function will return a two-tuple mapping a GetFile instance to a discovered
        hostname. This avoids code duplication in do_download and do_get_status.
        """
        get_files: List[GetFile] = []
        with click_spinner.spinner():
            for batch_get_cmd_req_id in batch_get_cmd_req_ids:
                get_files.extend(
                    self.batch_session.get_status_by_req_id(
                        batch_get_cmd_req_id=batch_get_cmd_req_id,
                        timeout=self.timeout,
                    )
                )

        if not get_files:
            return None

        self.last_batch_get_completed_uploads = 0

        # We first iterate over every GetFile to see whether we have the relevant device's name
        # cached in memory. If we do not, we'll try to get that information in batch from the
        # Hosts API before we attempt to download anything.
        aids_without_hostnames: List[str] = []
        for get_file in get_files:
            if get_file.device_id not in self.device_data:
                aids_without_hostnames.append(get_file.device_id)

        if aids_without_hostnames:
            self.device_data.update(
                self.client.hosts.get_device_data(device_ids=aids_without_hostnames),
            )

        get_file_data: List[Tuple[GetFile, str]] = []

        for get_file in get_files:
            # It's possible to be connected to a nameless device if the device is not properly
            # communicating with the cloud, so we assume we cannot get a name.
            hostname = "NO-HOSTNAME"

            # Attempt to get this device's name from the data cached in memory
            device_data = self.device_data.get(get_file.device_id)
            if device_data:
                hostname = device_data.get("hostname", "NO-HOSTNAME")

            self.poutput(
                f"{Fore.BLUE}Upload from {get_file.device_id} ({hostname}){Fore.RESET}\n"
                f"{Style.DIM}{Fore.WHITE}{get_file.filename} (SHA256 hash: {get_file.sha256})\n"
                f"Uploaded bytes: {get_file.size}{Style.RESET_ALL}"
            )

            self.last_batch_get_completed_uploads += 1

            get_file_data.append((get_file, hostname))  # Adds a two-tuple to the list

        return get_file_data

    def write_result_row(
        self,
        command: str,
        aid: str,
        complete: bool,
        stdout: str,
        stderr: str
    ):
        """Write a row of output to the CSV log file."""
        hostname = self.device_data[aid].get("hostname", "<NO HOSTNAME>")
        row = {
            'n': self.output_line_n,
            'command': command,
            'aid': aid,
            'hostname': hostname,
            'complete': complete,
            'stdout': stdout,
            'stderr': stderr,
        }
        self.csv_writer.writerow(row)
        self.output_line_n += 1

    def send_generic_command(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """Execute an arbitrary RTR command on the hosts within the session set.

        This function is used by other RTR commands to implement simple shell -> RTR command
        translation, execute the command, then return the results with minimal duplicate
        code.

        The function returns a two-tuple of (stdout, stderr), where each string is
        nullable. The values are derived from the first system in the list returned
        by the API to execute a command with complete = True. This is typically
        only a system that is actually online, as opposed to one available via
        the queueing functionality.
        """
        click.echo(click.style("Executing command: ", bold=True), nl=False)
        click.echo(command)
        with click_spinner.spinner():
            batch_results = self.batch_session.run_generic_command(
                command_string=command,
                timeout=self.timeout,
            )

        printed_first = False
        batch_result_count = len(batch_results.keys())
        outputs: Optional[Tuple[Optional[str], Optional[str]]] = None
        error_msg_set = set()
        for aid, batch_result in batch_results.items():
            complete = batch_result['complete']
            stdout = batch_result['stdout']
            stderr = batch_result['stderr']
            self.write_result_row(
                command=command,
                aid=aid,
                complete=complete,
                stdout=stdout,
                stderr=stderr,
            )

            if complete and not outputs:
                # We set stdout and stderr together, so that we do not end up with stdout from
                # one host and stderr from another
                outputs = (stdout, stderr)

            if not printed_first:
                hostname = self.device_data[aid].get("hostname", "<NO HOSTNAME>")
                self.poutput(f'{hostname}: {stdout}')
                self.perror(f'{Fore.RED}{hostname}: {stderr}{Fore.RESET}')

                printed_first = True

            if 'errors' in batch_result and batch_result['errors']:
                error_msg_set.add(batch_result['errors'][0]['message'])

        if batch_result_count > 1:
            self.poutput(
                f'(Output from the remaining {batch_result_count - 1} '
                'host(s) was written to the CSV output file)'
            )

        if error_msg_set:
            self.poutput(
                Fore.RED +
                "At least one error was detected. Check the log file for full details."
            )
            self.poutput(Fore.WHITE + "List of errors detected:")
            for err in error_msg_set:
                self.poutput(f'-> {Style.DIM}{err}')

        if outputs is None:
            return (None, None)

        # Flush the CSV after each command to keep the spreadsheet up to date
        self.csv_file_handle.flush()

        return outputs

    @with_argparser(PARSERS.cat, preserve_quotes=True)
    def do_cat(self, args):
        """Read a file from disk and display as ASCII or hex."""
        if args.show_hex:
            command = f'cat {args.file} -ShowHex'
        else:
            command = f'cat {args.file}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.cd, preserve_quotes=True)
    def do_cd(self, args):
        """Change the current working directory."""
        command = f'cd {args.directory}'
        new_directory, _ = self.send_generic_command(command)

        # Handle the case when no valid directory is returned
        if new_directory:
            self._set_prompt(new_directory)

    @with_argparser(PARSERS.cloud_scripts, preserve_quotes=False)
    def do_cloud_scripts(self, args):
        """List scripts saved in the cloud. These can be run with runscript -CloudFile."""
        scripts = self.client.rtr.query_scripts()
        sorted_scripts = sorted(
            scripts.items(),
            key=lambda x: x[1]['name'],
        )

        if args.script_name:
            found_script = False

        # Since we've made this API call, we might as well update the
        # choices for the parser, too.
        CLOUD_SCRIPT_CHOICES.clear()
        for script in sorted_scripts:
            script = script[1]
            CLOUD_SCRIPT_CHOICES.append(script['name'])

            # Only show script information if the name matches
            # what was requested by the user
            if args.script_name:
                if script['name'] == args.script_name:
                    found_script = True
                else:
                    continue

            self.poutput(
                Style.BRIGHT + Fore.BLUE + script['name'] + Style.RESET_ALL
            )

            creator_length = max(
                len(script['created_by']),
                len(script['modified_by']),
            )
            self.poutput(
                f"{Style.BRIGHT}created by:  {Fore.RED}"
                f"{script['created_by']:{creator_length}}{Style.RESET_ALL} "
                f"// {Style.BRIGHT}created at:  {Style.RESET_ALL}{Fore.RED}"
                f"{script['created_timestamp']}{Style.RESET_ALL}"
            )
            self.poutput(
                f"{Style.BRIGHT}modified by: {Fore.RED}"
                f"{script['modified_by']:{creator_length}}{Style.RESET_ALL} "
                f"// {Style.BRIGHT}modified at: {Style.RESET_ALL}{Fore.RED}"
                f"{script['modified_timestamp']}{Style.RESET_ALL}"
            )

            self.poutput(
                Style.BRIGHT + "Script length: " + Style.RESET_ALL +
                str(script['size']) + " bytes"
            )
            if 'description' in script:
                self.poutput(
                    Style.RESET_ALL + script['description']
                )

            if args.show_content:
                self.poutput(Fore.CYAN + script['content'] + Style.RESET_ALL)

            self.poutput()

        if args.script_name and not found_script:
            self.perror(f"The script {args.script_name} could not be found")

    @with_argparser(PARSERS.cp, preserve_quotes=True)
    def do_cp(self, args):
        """Copy a file or directory."""
        command = f'cp {args.source} {args.destination}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.csrutil, preserve_quotes=True)
    def do_csrutil(self, args):
        """[macOS] Display the System Integrity Protection status."""
        self.send_generic_command("csrutil")

    @with_argparser(PARSERS.cswindiag, preserve_quotes=True)
    def do_cswindiag(self, args):
        """[Windows] Execute the CSWinDiag tool to check for issues in a Falcon installation."""
        self.send_generic_command("cswindiag")

    @with_argparser(PARSERS.encrypt, preserve_quotes=True)
    def do_encrypt(self, args):
        """Encrypt a file with AES-256."""
        if args.key:
            command = f'encrypt {args.path} {args.key}'
        else:
            command = f'encrypt {args.path}'

        self.send_generic_command(command)

    @with_argparser(PARSERS.env, preserve_quotes=True)
    def do_env(self, args):
        """Get environment variables for all scopes (Machine / User / Process)."""
        self.send_generic_command("env")

    @with_argparser(PARSERS.eventlog, preserve_quotes=True)
    def do_eventlog(self, args):
        """[Windows] Inspect event logs. Subcommands: backup, export, list, view."""
        if args.command_name == "backup":
            command = f'eventlog backup {args.name} {args.filename}'
        elif args.command_name == "export":
            command = f'eventlog export {args.name} {args.filename}'
        elif args.command_name == "list":
            command = 'eventlog list'
        elif args.command_name == "view":
            if args.source_name and not args.count:
                self.perror(
                    Fore.RED +
                    "You must specify an event count if you specify a "
                    "source name. This is for RTR reasons."
                )
                return
            command = f'eventlog view {args.name}'
            if args.count:
                command = f'{command} {args.count}'
            if args.source_name:
                command = f'{command} {args.source_name}'

        self.send_generic_command(command)

    @with_argparser(PARSERS.filehash, preserve_quotes=True)
    def do_filehash(self, args):
        """Generate the MD5, SHA1, and SHA256 hashes of a file."""
        command = f'filehash {args.file}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.get, preserve_quotes=True)
    def do_get(self, args):
        """Upload a file to the CrowdStrike cloud from every connected host."""
        with click_spinner.spinner():
            batch_get_cmd_reqs_objs: List[BatchGetCmdRequest] = self.batch_session.get(
                file_path=args.file,
                timeout=self.timeout,
            )

        self.last_batch_get_cmd_req_ids = []
        resources = {}
        for batch_get_cmd_req_obj in batch_get_cmd_reqs_objs:
            if not batch_get_cmd_req_obj.batch_get_cmd_req_id:
                continue
            self.last_batch_get_cmd_req_ids.append(batch_get_cmd_req_obj.batch_get_cmd_req_id)
            resources.update(batch_get_cmd_req_obj.devices)

        if not resources:
            self.perror(Fore.RED + "The requested file does not exist on any connected hosts")
            return

        self.poutput(f"{Fore.BLUE}Initialised batch get requests with IDs:{Fore.RESET}")
        for batch_get_cmd_req in self.last_batch_get_cmd_req_ids:
            self.poutput(f"- {batch_get_cmd_req}")

        self.poutput("Use the get_status command to check the batch IDs shown above")

        self.last_batch_get_successful_requests = 0
        self.last_batch_get_completed_uploads = 0
        for host_id, get_data in resources.items():
            # If the command could be sent to the host, it is complete
            complete = get_data['complete']
            # stdout from a get shows the name of the file to be uploaded
            stdout = get_data['stdout']
            # stderr will show us if this failed, and why
            stderr = get_data['stderr']
            # See if the request was queued for the future
            queued = get_data['offline_queued']

            # All successful requests print the filename to stdout and stderr is left empty.
            # We also only count a successful result if it is not queued.
            successful = bool(stdout and not queued)

            if queued:
                stdout = "[QUEUED] " + stdout

            self.write_result_row(
                command="batch_get",
                aid=host_id,
                complete=complete,
                stdout=stdout,
                stderr=stderr,
            )
            if successful:
                self.last_batch_get_successful_requests += 1

    @with_argparser(PARSERS.get_status, preserve_quotes=False)
    def do_get_status(self, args):
        """Check the status of a batch get command."""
        if args.batch_get_req_id:
            get_file_data = self._search_get_files([args.batch_get_req_id])
        elif self.last_batch_get_cmd_req_ids:
            get_file_data = self._search_get_files(self.last_batch_get_cmd_req_ids)
        else:
            self.poutput(
                Fore.RED +
                "You must execute a batch get command first, or supply a "
                "batch get request ID"
            )
            return

        if not get_file_data:
            self.poutput(f'{Fore.YELLOW}No GET files in that batch have been uploaded.{Fore.RESET}')

    @with_argparser(PARSERS.download, preserve_quotes=False)
    def do_download(self, args):
        """Download files from the Falcon cloud obtained via a get command."""
        if not os.path.isdir(args.destination):
            self.poutput(f"{Fore.RED}{args.destination} is not a valid directory{Style.RESET_ALL}")
            return

        if args.batch_get_req_id:
            get_file_data = self._search_get_files([args.batch_get_req_id])
        elif self.last_batch_get_cmd_req_ids:
            get_file_data = self._search_get_files(self.last_batch_get_cmd_req_ids)
        else:
            self.poutput(
                Fore.RED +
                "You must execute a batch get command first, or supply a "
                "batch get request ID"
            )
            return

        if not get_file_data:
            self.poutput(
                f'{Fore.YELLOW}No GET files in that batch are available '
                f'for download yet.{Fore.RESET}'
            )
            return

        for get_file, hostname in get_file_data:
            self.poutput(
                f"{Fore.BLUE}Downloading {get_file.filename} from {hostname} "
                f"(AID: {get_file.device_id}){Fore.RESET}"
            )
            out_filename = output_file_name(get_file, hostname)
            full_filepath = os.path.join(args.destination, out_filename)
            with click_spinner.spinner():
                get_file.download(
                    output_path=full_filepath,
                    extract=args.extract_7z,
                    preserve_7z=False,
                )
            details = (
                f"destination={args.destination} | "
                f"extracted={str(args.extract_7z)} | "
                f"sha256={get_file.sha256}"
            )
            self.write_result_row(
                command="download",
                aid=get_file.device_id,
                complete=True,
                stdout=get_file.filename,
                stderr=details,
            )

        self.csv_file_handle.flush()

    @with_argparser(PARSERS.getsid, preserve_quotes=True)
    def do_getsid(self, args):
        """[Windows/macOS] Enumerate local users and Security Identifiers (SID)."""
        self.send_generic_command("getsid")

    @with_argparser(PARSERS.ifconfig, preserve_quotes=True)
    def do_ifconfig(self, args):
        """[Linux/macOS] Show network configuration information."""
        self.send_generic_command("ifconfig")

    @with_argparser(PARSERS.ipconfig, preserve_quotes=True)
    def do_ipconfig(self, args):
        """[Windows] Show network configuration information."""
        self.send_generic_command("ipconfig")

    @with_argparser(PARSERS.ls, preserve_quotes=True)
    def do_ls(self, args):
        """Display the contents of the specified path."""
        command = f'ls {args.directory}'

        if args.long_format:
            command += ' -l'

        if args.follow_symlinks:
            command += ' -L'

        if args.recursive:
            command += ' -R'

        if args.sort_time_modified:
            command += ' -T'

        self.send_generic_command(command)

    @with_argparser(PARSERS.kill, preserve_quotes=True)
    def do_kill(self, args):
        """Kill a process."""
        command = f'kill {args.pid}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.map, preserve_quotes=True)
    def do_map(self, args):
        """[Windows] Map an SMB (network) share drive."""
        command = f"map {args.drive_letter} {args.network_share} {args.username} {args.password}"
        self.send_generic_command(command)

    @with_argparser(PARSERS.memdump, preserve_quotes=True)
    def do_memdump(self, args):
        """[Windows] Dump the memory of a process."""
        if args.filename:
            command = f'memdump {args.pid} {args.filename}'
        else:
            command = f'memdump {args.pid}'

        self.send_generic_command(command)

    @with_argparser(PARSERS.mkdir, preserve_quotes=True)
    def do_mkdir(self, args):
        """Create a new directory."""
        command = f'mkdir {args.directory}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.mv, preserve_quotes=True)
    def do_mv(self, args):
        """Move a file or directory."""
        command = f'mv {args.source} {args.destination}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.netstat, preserve_quotes=True)
    def do_netstat(self, args):
        """Display network statistics and active connections."""
        if args.routing_info:
            command = "netstat -nr"
        else:
            command = "netstat"

        self.send_generic_command(command)

    @with_argparser(PARSERS.ps, preserve_quotes=True)
    def do_ps(self, args):
        """Display process information."""
        self.send_generic_command("ps")

    @with_argparser(PARSERS.put, preserve_quotes=True)
    def do_put(self, args):
        """Put a file from the CrowdStrike cloud onto the machine."""
        command = f'put {args.file}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.put_and_run, preserve_quotes=True)
    def do_put_and_run(self, args):
        """[Windows] Download and immediately execute a file from the CrowdStrike Cloud."""
        command = f'put-and-run {args.file}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.put_files, preserve_quotes=False)
    def do_put_files(self, args):
        """List the PUT files available in the Falcon instance."""
        put_files = self.client.rtr.query_put_files()
        sorted_put_files = sorted(
            put_files.items(),
            key=lambda x: x[1]['name'],
        )
        # Since we've made this API call, we might as well update the
        # choices for the parser, too.
        PUT_FILE_CHOICES.clear()
        for put_file in sorted_put_files:
            put_file = put_file[1]
            self.poutput(
                Style.BRIGHT + Fore.BLUE + put_file['name'] + Style.RESET_ALL
            )
            PUT_FILE_CHOICES.append(put_file['name'])
            creator_length = max(
                len(put_file['created_by']),
                len(put_file['modified_by']),
            )
            self.poutput(
                f"{Style.BRIGHT}created by:  {Fore.RED}"
                f"{put_file['created_by']:{creator_length}}{Style.RESET_ALL} "
                f"// {Style.BRIGHT}created at:  {Style.RESET_ALL}{Fore.RED}"
                f"{put_file['created_timestamp']}"
            )
            self.poutput(
                f"{Style.BRIGHT}modified by: {Fore.RED}"
                f"{put_file['modified_by']:{creator_length}}{Style.RESET_ALL} "
                f"// {Style.BRIGHT}modified at: {Style.RESET_ALL}{Fore.RED}"
                f"{put_file['modified_timestamp']}"
            )

            self.poutput(
                Style.BRIGHT + "File Size: " + Style.RESET_ALL +
                str(put_file['size']) + " bytes"
            )
            if 'description' in put_file:
                self.poutput(
                    Style.RESET_ALL + put_file['description']
                )
            self.poutput()

    @with_argparser(PARSERS.reg, preserve_quotes=True)
    def do_reg(self, args):
        """[Windows] Registry manipulation. Subcommands: delete, load, query, set, unload."""
        try:
            command = reg_builder(args)
        except CommandBuilderException as ex:
            self.perror(ex)
            return

        self.send_generic_command(command)

    @with_argparser(PARSERS.restart)
    def do_restart(self, args):
        """Restart target systems."""
        if args.confirm:
            self.send_generic_command("restart -Confirm")
        else:
            self.poutput(
                Fore.YELLOW +
                "You must confirm a restart with -Confirm. "
                "No action was taken."
            )

    @with_argparser(PARSERS.rm, preserve_quotes=True)
    def do_rm(self, args):
        """Remove (delete) a file or directory."""
        if args.force:
            command = f'rm {args.path} -Force'
        else:
            command = f'rm {args.path}'

        self.send_generic_command(command)

    @with_argparser(PARSERS.run, preserve_quotes=False)
    def do_run(self, args):
        """Run an executable."""
        command = f'run "{args.executable}"'

        if args.command_line_args:
            command = f'{command} -CommandLine=```{args.command_line_args}```'

        if args.wait:
            command = f'{command} -Wait'

        self.send_generic_command(command)

    @with_argparser(PARSERS.runscript, preserve_quotes=False)
    def do_runscript(self, args):
        """Run a PowerShell script."""
        # Handle Cloud Files first
        if args.cloud_file:
            command = f"runscript -CloudFile=\"{args.cloud_file}\""
        elif args.host_path:
            command = f"runscript -HostPath=\"{args.host_path}\""
        elif args.raw_script:
            command = f"runscript -Raw=```{args.raw_script}```"
        elif args.workstation_path:
            if (
                os.path.exists(args.workstation_path) and
                os.path.isfile(args.workstation_path)
            ):
                with open(args.workstation_path, 'rt', encoding='utf8') as script_file_handle:
                    contents = script_file_handle.read()
                command = f"runscript -Raw=```{contents}```"
            else:
                self.poutput(
                    f"{args.workstation_path} could not be found; "
                    "command aborted."
                )
                return

        if args.command_line_args:
            command = f"{command} -CommandLine=```{args.command_line_args}```"

        if args.script_timeout:
            command = f"{command} -Timeout={args.script_timeout}"

        self.send_generic_command(command)

    @with_argparser(PARSERS.shutdown)
    def do_shutdown(self, args):
        """Shutdown target systems."""
        if args.confirm:
            self.send_generic_command("shutdown -Confirm")
        else:
            self.poutput(
                Fore.YELLOW +
                "You must confirm a shutdown with -Confirm. "
                "No action was taken."
            )

    @with_argparser(PARSERS.tar, preserve_quotes=True)
    def do_tar(self, args):
        """[Linux] Compress a file or directory into a tar file."""
        tar_file = args.filename
        mode = "-c" if args.create else "-u"
        source = args.source
        if args.auto:
            compression = "-a"
        elif args.gzip:
            compression = "-z"
        elif args.bzip2:
            compression = "-j"
        elif args.lzma:
            compression = "-J"
        else:
            compression = None

        command = f"tar -f={tar_file} {mode} {source}"
        if compression:
            command = f"{command} {compression}"

        self.send_generic_command(command)

    @with_argparser(PARSERS.unmap, preserve_quotes=True)
    def do_unmap(self, args):
        """Unmap an SMB (network) share drive."""
        command = f'unmap {args.drive_letter}'
        self.send_generic_command(command)

    @with_argparser(PARSERS.update, preserve_quotes=True)
    def do_update(self, args):
        """[Windows] Windows update manipulation. Subcommands: history, install, list, query."""
        if args.command_name == "history":
            command = 'update history'
        elif args.command_name == "install":
            command = f'update install {args.kb}'
        elif args.command_name == "list":
            command = 'update list'
        elif args.command_name == "query":
            command = f'update query {args.kb}'
        else:
            self.poutput("Incorrect mode specified")
            return

        self.send_generic_command(command)

    @with_argparser(PARSERS.xmemdump, preserve_quotes=True)
    def do_xmemdump(self, args):
        """Dump the complete or kernel memory of the target systems."""
        if args.destination:
            command = f'xmemdump {args.mode} {args.destination}'
        else:
            command = f'xmemdump {args.mode}'

        self.send_generic_command(command)

    @with_argparser(PARSERS.zip, preserve_quotes=True)
    def do_zip(self, args):
        """Compress a file or directory into a zip file."""
        command = f'zip {args.source} {args.destination}'
        self.send_generic_command(command)
