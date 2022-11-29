"""Falcon Toolkit: Shell.

This file contains a timer which is instantiated by the main shell. This timer will keep calling
the auto_refresh_sessions function within Caracara to ensure that the RTR shell sessions never
expire.

This allows users to step away from the keyboard while a long operation runs and return to a shell
that has not timed out.
"""
from threading import Timer

from caracara.modules.rtr import RTRBatchSession


class SessionRefreshTimer:
    """RTR Session Refresh Timer object.

    The code within this class will refresh RTR batch sessions at a regular interval. Each call to
    Caracara's auto_refresh_sessions function will check first whether each 'inner' session is close
    to expiry and, in each case where this is the case, the batch sessions will be refreshed
    in this separate thread to keep the shell active.

    Code adapted from: https://stackoverflow.com/a/38317060
    """

    def __init__(
        self,
        interval: int,
        batch_session: RTRBatchSession,
        timeout: int = 30,
    ):
        """Initialise a timer object with parameters provided by the RTRPrompt object."""
        self._timer = None
        self.interval = interval
        self.batch_session = batch_session
        self.timeout = timeout
        self.is_running = False
        self.start()

    def _run(self):
        """Execute on the timer being triggered."""
        self.is_running = False
        self.start()
        self.batch_session.auto_refresh_sessions(self.timeout)

    def start(self):
        """Start the timer's waiting period."""
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """Gracefully shut the internal timer down."""
        self._timer.cancel()
        self.is_running = False
