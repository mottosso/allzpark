
import os
import unittest
import contextlib


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


def wait(timeout=1000):
    from allzpark.vendor.Qt import QtCore

    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()

    timer.timeout.connect(loop.quit)
    timer.start(timeout)
    loop.exec_()


@contextlib.contextmanager
def wait_signal(signal, on_value=None, timeout=1000):
    from allzpark.vendor.Qt import QtCore

    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    state = {"received": False}

    if on_value is None:
        def trigger(*args):
            state["received"] = True
            timer.stop()
            loop.quit()
    else:
        def trigger(value):
            if value == on_value:
                state["received"] = True
                timer.stop()
                loop.quit()

    def on_timeout():
        loop.quit()
        raise Exception("Signal waiting timeout.")

    signal.connect(trigger)
    timer.timeout.connect(on_timeout)

    try:
        yield
    finally:
        if not state["received"]:
            timer.start(timeout)
            loop.exec_()
