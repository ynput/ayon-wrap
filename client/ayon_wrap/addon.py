import os

from openpype.modules import OpenPypeModule, IHostAddon
from openpype.lib import Logger

log = Logger.get_logger("Wrap")
WRAP_HOST_DIR = os.path.dirname(os.path.abspath(__file__))


class WrapAddon(OpenPypeModule, IHostAddon):
    name = "wrap"
    host_name = "wrap"

    def initialize(self, module_settings):
        self.enabled = True

    def get_workfile_extensions(self):
        return [".wrap"]

    def get_launch_hook_paths(self, app):
        if app.host_name != self.host_name:
            return []
        return [
            os.path.join(WRAP_HOST_DIR, "hooks")
        ]
