from openpype.modules import OpenPypeModule, IHostAddon
from openpype.lib import Logger

log = Logger.get_logger("Wrap")


class WrapAddon(OpenPypeModule, IHostAddon):
    name = "wrap"
    host_name = "wrap"

    def initialize(self, module_settings):
        self.enabled = True

    def get_workfile_extensions(self):
        return [".wrap"]
