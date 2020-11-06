
import os
import unittest


MEMORY_LOCATION = "memory@any"


class TestBase(unittest.TestCase):

    def setUp(self):
        from allzpark import cli

        os.environ["ALLZPARK_PREFERENCES_NAME"] = "preferences_test"
        os.environ["REZ_PACKAGES_PATH"] = MEMORY_LOCATION

        app, ctrl = cli.initialize(clean=True, verbose=3)
        window = cli.launch(ctrl)

        self.app = app
        self.ctrl = ctrl
        self.window = window

    def tearDown(self):
        wait(timeout=500)
        self.window.close()


def memory_repository(packages):
    from allzpark import _rezapi as rez

    manager = rez.package_repository_manager
    repository = manager.get_repository(MEMORY_LOCATION)
    repository.data = packages


def wait(signal=None, on_value=None, timeout=1000):
    from allzpark.vendor.Qt import QtCore

    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    state = {"timeout": False}

    if on_value:
        def trigger(value):
            if value == on_value:
                loop.quit()
                state["timeout"] = False
    else:
        def trigger(*args):
            loop.quit()
            state["timeout"] = False

    if signal is not None:
        state["timeout"] = True
        signal.connect(trigger)
    timer.timeout.connect(loop.quit)

    timer.start(timeout)
    loop.exec_()

    if state["timeout"]:
        raise Exception("Signal waiting timeout.")
