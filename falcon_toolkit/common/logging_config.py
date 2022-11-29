"""Falcon Toolkit: Logging Configuration.

The toolkit provides extremely detailed logging. This class configures the global logger to
capture logs from both the toolkit itself, as well as Caracara behind the scenes.
All logs are compressed using gzip to keep file sizes down.
"""
import datetime
import gzip
import logging
import logging.handlers
import os


from falcon_toolkit.common.constants import (
    LOG_CONSOLE_FORMATTER,
    LOG_FILE_DATE_FORMAT,
    LOG_FILE_OUTPUT_FORMAT,
)


def configure_logger(
    log_path: str,
    log_level: int = logging.INFO,
    log_compression: bool = True,
) -> str:
    """Configure the Falcon Toolkit logger based on the user's preferences."""
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%dT%H_%M_%S.%f")
    # We preserve most of the log filename (including path) for RTR CSV outputs
    log_filename_base = os.path.join(
        log_path,
        f"FalconToolkit_{timestamp_str}"
    )
    log_filename = log_filename_base + ".log"
    if log_compression:
        log_filename += ".gz"
        # Gzip compress the main log file on the fly via a memory stream.
        # This is required to avoid the gzip file from being corrupted if the
        # the script ends prematurely (e.g, it crashes).
        log_output_file = gzip.open(log_filename, mode='wt', encoding='utf-8')
        stream_handler = logging.StreamHandler(log_output_file)
        memory_handler = logging.handlers.MemoryHandler(
            capacity=1024,
            flushLevel=log_level,
            target=stream_handler,
        )
        logging.basicConfig(
            level=logging.DEBUG,
            datefmt=LOG_FILE_DATE_FORMAT,
            format=LOG_FILE_OUTPUT_FORMAT,
            handlers=[memory_handler],
            encoding='utf-8',
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=LOG_FILE_OUTPUT_FORMAT,
            datefmt=LOG_FILE_DATE_FORMAT,
            filename=log_filename,
            filemode='wt',
        )

    console = logging.StreamHandler()
    console.setLevel(level=log_level)
    console_formatter = logging.Formatter(LOG_CONSOLE_FORMATTER)
    console.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console)

    logging.debug("Logger configured")
    return log_filename_base
