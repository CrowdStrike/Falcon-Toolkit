# Falcon Toolkit

![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)
[![PyPI](https://img.shields.io/pypi/v/Falcon-Toolkit)](https://pypi.org/project/Falcon-Toolkit)
![OSS Lifecycle](https://img.shields.io/osslifecycle/CrowdStrike/Falcon-Toolkit)

***automate all the things...remotely!***

## What Is This?

*Falcon Toolkit* is an all in one toolkit designed to make your Falcon life much easier. It is built on top of [Caracara](https://github.com/CrowdStrike/caracara).

The toolkit provides:

- Host searching, with filter support.
- Multiple profile support, including support for MSSP / Falcon Flight Control configurations.
- A shell allowing you to interface with many hosts via RTR at once, and get the output via CSV.
- Scriptability! You can program the shell by providing pre-written routines via a file on disk, and a full Python extensibility API is provided.
- More functionality is coming soon! Already on the roadmap are Policy import/export and IOA import/export. Want more functionality? Open an [Issue](https://github.com/CrowdStrike/Falcon-Toolkit/issues/new)!

Since this is built on top of Caracara, you get a bunch of great functionality and flexibility free, including the ability to filter hosts using dynamically generated FQL queries, full debug logging where desired, Falcon Flight Control integration, and more! Plus, the tool is lightning quick as it leverages Caracara's parallelisation tricks to pull more information quickly.

## Basic Concepts

Falcon Toolkit requires you to pre-configure profiles, consisting of:

- A name (such as for a client or Falcon tenant);
- An optional description;
- A Falcon API client ID;
- A corresponding Falcon API client secret; and
- Optionally, the desired cloud, although this can be automatically figured out based on magic provided by [FalconPy](https://falconpy.io) provided you are not a GovCloud customer.

Once these options are configured, you do not need to specify a client ID/secret again for communicating with that client. The configurations are saved in the file `~/FalconToolkit/FalconToolkit.json`, and the client secret for each corresponding client ID is stored in your host's local secure storage environment (e.g., via DPAPI on Windows, the Keychain on macOS, or Gnome's secret store on Linux). This keeps your client secrets secure and encrypted using your logon password.

Once you are within an RTR shell, you can run any command that you can run within standard RTR, with full usage, tab completion and examples. However, note that some commands (such as `reg` and `runscript`) have been slightly adjusted in their usage to match standard Unix command patterns. There are technical reasons for this; reach out to me if you need support. Furthermore, some commands have been augmented or added, such as `runscript -WorkstationPath` which allows you to run a local script without making it a cloud file first, `get_status` to check on file uploads, and `download` to pull files retrieved via `get` down to your local system.

## Getting Started

This tool is built using [Poetry](https://python-poetry.org) and Python 3. Therefore, you must first ensure that you have both Poetry and Python 3.9+ installed to make use of this tool. Ensure you pay attention to Step 3 of the [Poetry installation instructions](https://python-poetry.org/docs/master/#installing-with-the-official-installer) so that you get Poetry added to your shell's `PATH` variable.

Once Poetry is installed and loaded in your shell, simply clone this repository from GitHub and run `poetry install` within the `Falcon-Toolkit` directory to get all the necessary requirements set up in a virtual environment.

Next, run  `poetry shell` to enter the virtual environment.

Finally, run the `falcon` command to get started! If this succeeds and you get some help output, you're ready to go.

If you close your shell, simply run `poetry shell` to get back in to the virtual environment. This will bring back the `falcon` command.

You will soon be able to install this with `pip`. Watch this space as we get this configured!

## Updating the Toolkit

To update Falcon Toolkit, run `git pull` to get the latest code from the `main` branch, then run `poetry install` to get the latest requirements configured.

### Creating a New Profile

The command `falcon profiles new` will guide you through creating a new configuration. Note that:

- The name you specify will be the one you use to start a shell, so if you put a space in it remember that you'll need to wrap it in quotes later. Therefore, we do not recommend using a space here.
- The client ID and secret you specify must have full RTR admin and host querying permissions enabled; otherwise, this tool will not be able to execute any commands.

Two types of configuration backends are provided out of the box: the default, which is for an API keypair associated with a standard Falcon tenant, and a Falcon Flight Control backend. Use the Flight Control backend when authenticating to a Parent CID, as you will be able to specify the desired child CID on execution.

### Showing Your Profiles

The command `falcon profiles list` will show you all configurations (if any) you have created using the `new` command above, listed by the name you specified.

Example output:

```shell
$ falcon profiles list
Falcon Toolkit
Configuration Directory: /Users/username/FalconToolkit
Falcon Instance Configurations
ServicesTest
    Test instance for Services
```

### Deleting a Profile

The command `falcon profiles delete [Profile Name]` will delete a configuration for you. Use the name you defined when you created the profile via `falcon profiles new`.

### Selecting a Profile

If you have configured one profile, Falcon Toolkit will use it by default. If you have multiple profiles, you must select one using `-p`, like this:

```shell
$ falcon -p Profile2 <command> <command-specific params>
Falcon Toolkit
...
```

### Listing Filters

A key part of this tool (as we'll see later) is filter support. To see what filters are supported by the Falcon Toolkit and FalconPy, run `falcon filters`. Each filter is listed and explained with examples.

### Host Search

Before jumping into an RTR shell, you may wish to see which hosts you would connect to if you used the `shell` command (covered below). To do so, use the `falcon host_search` command.

As with the `shell` command, you must specify a profile (the name of a configuration you created using the `new` command above) if you have created more than one, and you can then optionally provide as many filters as you want using succesive `-f` switches. Some examples:

List all Windows hosts that are not within the `London` site, within the one Falcon instance configured earlier.

```shell
falcon host_search -f OS=Windows -f Site__NOT=London
```

List all Windows hosts not within the `075e03f5e5c04d83b4831374e7dc01c3` Group, wihtin the `MyCompany` Falcon tenant.

```shell
falcon -p MyCompany host_search -f OS=Windows -f GroupID__NOT=075e03f5e5c04d83b4831374e7dc01c3
```

List all `MyOtherCompany` Windows servers or domain controllers not within an OU called `Protected`

```shell
falcon -p MyOtherCompany host_search -f OS=Windows -f Role=Server,DC -f OU__NOT=Protected
```

List all `MyOtherCompany` Windows Workstations that have checked in to Falcon within the past 30 minutes

```shell
falcon -p MyOtherCompany host_search -f OS=Windows -f Role=Workstation -f LastSeen__GTE=-30m
```

### Jump into an RTR Shell

Now that you know how to filter, you know how to jump into a shell! To get into a batch shell with no special options, just do the same as for a `host_search` but use the `shell` command instead. For example, to launch an RTR shell with all Windows hosts last seen within the past 30 minutes within the `MyCompany` Falcon instance, use this command:

```shell
falcon -p MyCompany shell -f OS=Windows -f LastSeen__GTE=-30m
```

You can also specify an initial timeout to use for all RTR commands. By default, the timeout is 30 seconds, but you can change this to, e.g., 60 seconds, like this:

```shell
falcon -p MyCompany shell -f OS=Windows -t 60
```

Once in the shell, you can run `help` at any time to get a list of commands. Every command also supports the `-h` switch to find out how it works. Run `quit` at any time to get back to your command line.

All outputs are written to a log file, as well as a CSV alongside it showing the output from every host. If you run this tool against many hosts, you will see the output from the first in the list on screen. However, every host's output (from `stdout` and `stderr`) is written to the accompanying CSV.

All logs and CSVs are written to the `logs` folder within your configuration directory (default: `~/FalconToolkit`).

### Scripting

Remember we said you can script this? Well, here is how you do it!

#### Command Replay Script

If you have a file on disk with all shell commands you wish to run, you can specify it as a command line switch:

```shell
falcon shell -f OS=Windows -s script.rtr
```

This would run a script from disk called `script.rtr`. Scripts should end in the `quit` command if you do not wish to run further commands after your script has run (and therefore return to the shell).

Note that scripts contain a list of shell commands, *not* a list of zsh/PowerShell commands. Therefore, if you need to run a raw script command, write a script containing content like this:

```shell
runscript -Raw "Get-ChildItem"
quit
```

#### Python Scripting API

This tool is build on top of the excellent [Cmd2](https://cmd2.readthedocs.io/) Python library, which brings with it copious extensibility. It is possible to write Python scripts that run within the context of the Toolkit's shell with programmatic logic applied. This feature is very much in beta, and we are actively seeking feedback on which state data should be made available globally to aid in programmatic scripting of the shell.

Information on Cmd2's scripting backend is provided [here](https://cmd2.readthedocs.io/en/stable/features/scripting.html#python-scripts). The backend is configured as follows:

- The RTR Shell's application [bridge name](https://cmd2.readthedocs.io/en/stable/features/scripting.html#basics) is `rtr`, so `rtr("runscript -Raw \"Get-ChildItem\"")` would execute the `Get-ChildItem` PowerShell command against all connected systems from within a custom PyScript.
- The `self` functionality is enabled, enabling developers to introspect data stored within the RTR Shell itself. In this context, `self` will refer to the instantiated `RTRPrompt` object defined in `falcon_toolkit/shell/prompt.py`.

Some example usages of this functionality are as follows:

- Execute a batch `get` command and then cache the contents of `self.last_batch_get_successful_requests` to find out how many systems had the file on disk. Then, the script could wait `x` seconds in a loop up to a maximum amount of time, running `get_status` each time. On each iteration, the script may query `self.last_batch_get_completed_uploads` to determine whether a minimum threshold of systems have uploaded the requested file, and then once complete execute `download -e /some/output/folder` to pull those completed uploads down to a folder of choice (then extract them automatically).
- Execute a series of commands that differ by target OS, using the contents of `self.connected_devices` to make decisions dynamically.
- Execute `self.send_generic_command` directly, then use the returned `(stdout, stderr)` tuple to make decisions about which command to execute next (best suited to single system connections).

## Support & Community Forums

Falcon Toolkit is an open source project, and not a formal CrowdStrike product, designed to assist users with managing their Falcon tenants and executing commands at scale. As such, it carries no formal support, express or implied. This project originated out of the CrowdStrike Services Incident Response (IR) team's need to execute commands across Falcon tenants quickly, at scale, and with auditing, and is maintained by [Chris Hammond](mailto:Chris.Hammond@crowdstrike.com).

Is something going wrong? GitHub Issues are used to report bugs. Submit an [Issue](https://github.com/CrowdStrike/Falcon-Toolkit/issues/new/choose) and let us know what is happening.

Furthermore, GitHub Discussions provide the community with means to communicate.

*Security issues should be raised to our [Security team](mailto:security@crowdstrike.com) and [Chris Hammond](mailto:Chris.Hammond@crowdstrike.com).*

Thank you for using the Falcon Toolkit! We hope it is as useful to the Falcon user community as it is to us.
