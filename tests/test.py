
import os
import unittest
from allzpark import cli


def memory_repository(packages):
    from allzpark import _rezapi as rez

    repository = rez.package_repository_manager.get_repository("memory@any")
    repository.data = packages


def wait(signal):
    from allzpark.vendor.Qt import QtCore

    loop = QtCore.QEventLoop()

    signal.connect(lambda *args, **kwargs: loop.quit())
    loop.exec_()


class TestBase(unittest.TestCase):

    def setUp(self):
        os.environ["REZ_PACKAGES_PATH"] = "memory@any"

        app, ctrl = cli.initialize(clean=True)
        window = cli.launch(ctrl)

        self.app = app
        self.ctrl = ctrl
        self.window = window

    def tearDown(self):
        pass

    def test_last_profile_selected(self):
        memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                }
            },
            "bar": {
                "1.0.0": {
                    "name": "bar",
                    "version": "1.0.0",
                }
            }
        })
        self.ctrl.reset(["foo", "bar"])

        wait(self.ctrl.resetted)
        self.assertEqual("bar", self.ctrl.state["profileName"])
