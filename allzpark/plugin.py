
import logging
from .vendor.Qt import QtCore, QtWidgets


class EnvPluginBase(QtWidgets.QWidget):
    """Base class of environment plugin"""

    name = "Environment Plugin"

    envChanged = QtCore.Signal(dict)
    envReset = QtCore.Signal()
    revealed = QtCore.Signal()
    consoleShown = QtCore.Signal()
    logged = QtCore.Signal(str, int)  # message, level

    def on_profile_changed(self, package):
        """Runs on profile changed

        This will be called by Allzpark when profile has changed.
        Reimplement this function if you need plugin to take actions on
        profile change.

        Args:
            package: profile package

        """
        pass

    def on_application_changed(self, package):
        """Runs on application selection changed

        This will be called by Allzpark when selected application changed.
        Reimplement this function if you need plugin to take actions on
        application change.

        Args:
            package: application package

        """
        pass

    def validate(self, environ, package):
        """Validate environment before launching application

        This will be called by Allzpark when application is about to launch,
        and abort launching if validation failed with message returned.

        Return None if validation passed, or string message as reason why it
        fails. Returning any value that is not equivalent to False (e.g. None,
        "", 0) will be considered as fail and the value will be used to format
        string error message.

        Args:
            environ (dict): env vars that merged from parent, plugin and user
            package: application package that being launched

        Returns:
            None or str

        """
        pass

    def set_env(self, env):
        """Inject additional environment variables

        The `env` will be applied on top of parent environment, and user
        environment variables on top of it.

        Multi-path variable will simply be overwritten, no appending nor
        prepending.

        Args:
            env (dict): key-value paired environment variables

        Returns:
            None

        """
        self.envChanged.emit(env)

    def clear_env(self):
        """Reset additional environment variables

        Returns:
            None

        """
        self.envReset.emit()

    def reveal(self):
        """Activate plugin dock widget

        Show plugin dock widget. Could be used when input is required and
        need to have focus on the plugin page.

        Returns:
            None

        """
        self.revealed.emit()

    def to_console(self):
        """Activate Allzpark console dock widget

        Show Allzpark console dock widget. Could be used when there are log
        messages that need user to know.

        Returns:
            None

        """
        self.consoleShown.emit()

    def debug(self, message):
        """Send debug message to Allzpark console"""
        self.logged.emit(message, logging.DEBUG)

    def info(self, message):
        """Send regular message to Allzpark console"""
        self.logged.emit(message, logging.INFO)

    def warning(self, message):
        """Send warning message to Allzpark console"""
        self.logged.emit(message, logging.WARNING)

    def error(self, message):
        """Send error message to Allzpark console"""
        self.logged.emit(str(message), logging.ERROR)
