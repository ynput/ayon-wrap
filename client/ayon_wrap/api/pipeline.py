import os
import json

import pyblish.api

from openpype.lib import Logger
from openpype.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    AVALON_CONTAINER_ID
)

from openpype.host import (
    HostBase,
    ILoadHost,
)
from ayon_wrap import WRAP_HOST_DIR

log = Logger.get_logger(__name__)


PLUGINS_DIR = os.path.join(WRAP_HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")


class WrapHost(HostBase, ILoadHost):
    name = "wrap"

    def __init__(self, workfile_path):
        self._workfile_path = workfile_path
        super(WrapHost, self).__init__()

    def install(self):
        print("Installing Pype config...")

        pyblish.api.register_host("wrap")
        pyblish.api.register_plugin_path(PUBLISH_PATH)

        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        log.info(PUBLISH_PATH)

    def get_containers(self):
        """Get list of loaded containers.

        Containers are created by filling prepared placeholders with publish
        path of chosen representation and storing this metadata into the
        workfile.

        Returns:
            (list of dict with schema similar to "openpype:container-2.0" -
             "nodeId" added to point to node in Wrap)
        """
        with open(self._workfile_path, "r") as f:
            content = json.load(f)

            metadata = (content.get("metadata", {})
                               .get("AYON_NODE_METADATA", []))

        containers = []
        for item in metadata:
            if item["id"] == AVALON_CONTAINER_ID:
                containers.append(item)

        return containers


def containerise(name,
                 namespace,
                 context,
                 loader=None,
                 data=None):
    """
    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Creates dictionary payloads that gets saved into file metadata. Each
    container contains of who loaded (loader) and members (single or multiple
    in case of background).

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        context (dict): Asset information
        loader (str, optional): Name of loader used to produce this container.
        data (dict): additional data to store placeholder, nodeId and node_name

    Returns:
        container (str): Name of container assembly
    """
    data = {
        "schema": "openpype:container-2.0",
        "id": AVALON_CONTAINER_ID,
        "name": name,
        "namespace": namespace,
        "loader": str(loader),
        "representation": str(context["representation"]["_id"]),
        "original_value": data["original_value"],
        "nodeId": data["nodeId"],
        "objectName": data["node_name"]
    }

    return data


