
from unittest import mock
from tests import util


class TestProfiles(util.TestBase):

    def test_reset(self):
        """Test session reset
        """
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
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo", "bar"])

        # last profile will be selected by default
        self.assertEqual("bar", self.ctrl.state["profileName"])
        self.assertEqual(["foo", "bar"], list(self.ctrl.state["rezProfiles"]))

    def test_select_profile_with_out_apps(self):
        """Test selecting profile that has no apps
        """
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
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo", "bar"])

        with util.wait_signal(self.ctrl.state_changed, "noapps"):
            self.ctrl.select_profile("foo")
            # wait enter 'noapps' state

        self.assertEqual("foo", self.ctrl.state["profileName"])

    def test_profile_list_apps(self):
        """Test listing apps from profile
        """
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
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])

        with util.wait_signal(self.ctrl.state_changed, "ready"):
            self.ctrl.select_profile("foo")

        self.assertEqual(
            [
                "app_A==1.0.0",
                "app_B==1.0.0",
            ],
            list(self.ctrl.state["rezApps"].keys())
        )

    def test_profile_listing_without_root_err(self):
        """Listing profile without root will raise AssertionError"""
        self.assertRaises(AssertionError, self.ctrl.reset)
        self.assertRaises(AssertionError, self.ctrl.list_profiles)

    def test_profile_listing_callable_root_err(self):
        """Listing profile with bad callable will prompt error message"""
        import traceback
        import logging
        from allzpark import control

        traceback.print_exc = mock.MagicMock(name="traceback.print_exc")
        self.ctrl.error = mock.MagicMock(name="Controller.error")

        def bad_root():
            raise Exception("This should be caught.")
        self.ctrl.list_profiles(bad_root)

        # ctrl.error must be called in all cases
        self.ctrl.error.assert_called_once()
        # traceback.print_exc should be called if logging level is set
        # lower than INFO, e.g. DEBUG or NOTSET
        if control.log.level < logging.INFO:
            traceback.print_exc.assert_called_once()

    def test_profile_listing_invalid_type_root_err(self):
        """Listing profile with invalid input type will raise TypeError"""
        self.assertRaises(TypeError, self.ctrl.list_profiles, {"foo"})

    def test_profile_listing_filter_out_empty_names(self):
        """Listing profile with empty names will be filtered"""
        expected = ["foo", "bar"]
        profiles = self.ctrl.list_profiles(expected + [None, ""])
        self.assertEqual(profiles, expected)
