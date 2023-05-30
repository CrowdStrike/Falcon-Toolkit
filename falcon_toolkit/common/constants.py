"""Falcon Toolkit: Common Constants."""
import os

import platformdirs

# Authentication
KEYRING_SERVICE_NAME = "FalconToolkit"

# Configuration
CONFIG_FILENAME = "FalconToolkit.json"
DEFAULT_CONFIG_DIR = platformdirs.user_data_dir(
    appname="FalconToolkit",
    appauthor="CrowdStrike",
)
OLD_DEFAULT_CONFIG_DIR = os.path.expanduser("~/FalconToolkit")

# Logging
LOG_CONSOLE_FORMATTER = "%(message)s"
LOG_FILE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
LOG_FILE_OUTPUT_FORMAT = '%(asctime)s %(name)-24s %(levelname)-8s %(message)s'
LOG_SUB_DIR = "logs"
