import os

import pyblish.api

from openpype.lib import Logger
from openpype.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
)
import openpype.hosts.aftereffects

from openpype.host import (
    HostBase,
    IWorkfileHost,
    ILoadHost,
    IPublishHost
)


log = Logger.get_logger(__name__)


HOST_DIR = os.path.dirname(
    os.path.abspath(openpype.hosts.aftereffects.__file__)
)
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")


class WrapHost(HostBase, ILoadHost):
    name = "wrap"

    def __init__(self):
        self._stub = None
        super(WrapHost, self).__init__()

    def install(self):
        print("Installing Pype config...")

        pyblish.api.register_host("wrap")
        pyblish.api.register_plugin_path(PUBLISH_PATH)

        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        log.info(PUBLISH_PATH)

    def get_containers(self):
        return self.list_instances()

    def get_context_data(self):
        meta = self.stub.get_metadata()
        for item in meta:
            if item.get("id") == "publish_context":
                item.pop("id")
                return item

        return {}

    def list_instances(self):
        """List all created instances from current workfile which
        will be published.

        Pulls from File > File Info

        For SubsetManager

        Returns:
            (list) of dictionaries matching instances format
        """
        return []
