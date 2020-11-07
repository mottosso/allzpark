
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
        self.ctrl.reset(["foo"])
        util.wait(self.ctrl.resetted)

        self.ctrl.select_profile("foo")
        util.wait(self.ctrl.state_changed, "ready")

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

        self.ctrl.launch(command=command,
                         stdout=lambda m: stdout.append(m),
                         stderr=lambda m: stderr.append(m))

        util.wait(self.ctrl.state_changed, "launching")
        self.assertEqual(len(commands), 1)

        util.wait(commands[0].killed)
        self.assertIn("meow", "\n".join(stdout))
        self.assertEqual("", "\n".join(stderr))
