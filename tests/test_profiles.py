
import os
import unittest
from tests import util


class TestProfiles(unittest.TestCase):

    def setUp(self):
        from allzpark import cli

        os.environ["ALLZPARK_PREFERENCES_NAME"] = "preferences_test"
        os.environ["REZ_PACKAGES_PATH"] = util.MEMORY_LOCATION

        app, ctrl = cli.initialize(clean=True, verbose=3)
        window = cli.launch(ctrl)

        self.app = app
        self.ctrl = ctrl
        self.window = window

    def tearDown(self):
        pass

    def test_reset(self):
        """Test session reset"""
        util.memory_repository({
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

        util.wait(self.ctrl.resetted)

        # last profile will be selected by default
        self.assertEqual("bar", self.ctrl.state["profileName"])
        self.assertEqual(["foo", "bar"], list(self.ctrl.state["rezProfiles"]))

    def test_select_profile_with_out_apps(self):
        """Test selecting profile that has no apps"""
        util.memory_repository({
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
        util.wait(self.ctrl.resetted)

        self.ctrl.select_profile("foo")
        # enter 'noapps' state
        util.wait(self.ctrl.state_changed, "noapps")
        self.assertEqual("foo", self.ctrl.state["profileName"])

    def test_profile_list_apps(self):
        """Test listing apps from profile"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "lib_foo",
                        "~app_A",
                        "~app_B",
                    ],
                }
            },
            "app_A": {
                "1.0.0": {
                    "name": "app_A",
                    "version": "1.0.0",
                }
            },
            "app_B": {
                "1.0.0": {
                    "name": "app_B",
                    "version": "1.0.0",
                }
            },
            "lib_foo": {
                "1.0.0": {
                    "name": "lib_foo",
                    "version": "1.0.0",
                }
            },
        })
        self.ctrl.reset(["foo"])
        util.wait(self.ctrl.resetted)

        self.ctrl.select_profile("foo")
        util.wait(self.ctrl.state_changed, "ready")
        self.assertEqual(
            [
                "app_A==1.0.0",
                "app_B==1.0.0",
            ],
            list(self.ctrl.state["rezApps"].keys())
        )
