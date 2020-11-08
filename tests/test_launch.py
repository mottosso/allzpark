
import sys
from tests import util


class TestLaunch(util.TestBase):

    def test_launch_subprocess(self):
        """Test launching subprocess command"""
        util.memory_repository({
            "foo": {
                "1": {
                    "name": "foo",
                    "version": "1",
                    "requires": ["~app"],
                }
            },
            "app": {
                "1": {
                    "name": "app",
                    "version": "1",
                }
            },
        })
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])

        with util.wait_signal(self.ctrl.state_changed, "ready"):
            self.ctrl.select_profile("foo")

        self.ctrl.select_application("app==1")
        self.assertEqual("app==1", self.ctrl.state["appRequest"])

        commands = self.ctrl.state["commands"]
        self.assertEqual(len(commands), 0)

        stdout = list()
        stderr = list()
        command = (
          '%s -c "'
          'import sys;'
          'sys.stdout.write(\'meow\')"'
        ) % sys.executable

        with util.wait_signal(self.ctrl.state_changed, "launching"):
            self.ctrl.launch(command=command,
                             stdout=lambda m: stdout.append(m),
                             stderr=lambda m: stderr.append(m))

        self.assertEqual(len(commands), 1)

        with util.wait_signal(commands[0].killed):
            pass

        self.assertIn("meow", "\n".join(stdout))
        self.assertEqual("", "\n".join(stderr))
