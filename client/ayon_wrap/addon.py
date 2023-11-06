import os

from openpype.modules import OpenPypeModule, IHostAddon, IPluginPaths
from openpype.lib import Logger

log = Logger.get_logger("Wrap")
WRAP_HOST_DIR = os.path.dirname(os.path.abspath(__file__))
CREATE_PATH = os.path.join(WRAP_HOST_DIR, "plugins",  "create")
PUBLISH_PATH = os.path.join(WRAP_HOST_DIR, "plugins",  "publish")


class WrapAddon(OpenPypeModule, IHostAddon, IPluginPaths):
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

    def get_plugin_paths(self):
        return {
            "create": [],
            "publish": [],
            "load": []
        }

    def get_create_plugin_paths(self, host_name):
        if host_name == "traypublisher":
            return [CREATE_PATH]

    def get_publish_plugin_paths(self, host_name):
        if host_name == "traypublisher":
            return [PUBLISH_PATH]
