
import os
import unittest
from tests import util


class TestApps(unittest.TestCase):

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

    def test_select_app(self):
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
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
        })
        self.ctrl.reset(["foo"])
        util.wait(self.ctrl.resetted)

        self.ctrl.select_profile("foo")
        util.wait(self.ctrl.state_changed, "ready")

        env = self.ctrl.state["rezEnvirons"]

        # first app will be selected if no preference loaded
        self.assertEqual("app_A==1.0.0", self.ctrl.state["appRequest"])
        self.assertIn("app_A==1.0.0", env)
        self.assertNotIn("app_B==1.0.0", env)

        self.ctrl.select_application("app_B==1.0.0")

        self.assertEqual("app_B==1.0.0", self.ctrl.state["appRequest"])
        self.assertIn("app_A==1.0.0", env)
        self.assertIn("app_B==1.0.0", env)

    def test_app_environ(self):
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",
                        "~app_B",
                    ],
                    "commands": "env.FOO='BAR'"
                }
            },
            "app_A": {
                "1.0.0": {
                    "name": "app_A",
                    "version": "1.0.0",
                    "commands": "env.THIS_A='1'"
                }
            },
            "app_B": {
                "1.0.0": {
                    "name": "app_B",
                    "version": "1.0.0",
                    "commands": "env.THIS_B='1'"
                }
            },
        })
        self.ctrl.reset(["foo"])
        util.wait(self.ctrl.resetted)

        self.ctrl.select_profile("foo")
        util.wait(self.ctrl.state_changed, "ready")

        env = self.ctrl.state["rezEnvirons"]

        for app_request in ["app_A==1.0.0", "app_B==1.0.0"]:
            self.ctrl.select_application(app_request)

        self.assertIn("app_A==1.0.0", env)
        self.assertIn("app_B==1.0.0", env)

        # profile env will apply to all apps
        self.assertIn("FOO", env["app_A==1.0.0"])
        self.assertIn("FOO", env["app_B==1.0.0"])
        self.assertEqual(env["app_A==1.0.0"]["FOO"], "BAR")
        self.assertEqual(env["app_B==1.0.0"]["FOO"], "BAR")

        self.assertIn("THIS_A", env["app_A==1.0.0"])
        self.assertNotIn("THIS_A", env["app_B==1.0.0"])

        self.assertIn("THIS_B", env["app_B==1.0.0"])
        self.assertNotIn("THIS_B", env["app_A==1.0.0"])
