import json
import os.path

from ayon_core.pipeline import (
    LoaderPlugin,
    AVALON_CONTAINER_ID,
    get_current_context
)
from ayon_wrap.api import fill_placeholder, get_token_and_values


class FileLoader(LoaderPlugin):
    """Load images

    Stores the imported asset in a container named after the asset.
    """
    label = "Load file"

    # TODO
    families = ["image",
                "plate",
                "render",
                "prerender",
                "review",
                "model"]
    representations = ["*"]

    def load(self, context, name=None, namespace=None, data=None):
        # Loader currently not implemented, only SceneInventory
        raise NotImplementedError

    def update(self, container, representation):
        """ Switch asset or change version """
        context = get_current_context()

        nodeId = container["nodeId"]
        with open(container["namespace"], "r") as fp:
            content = json.load(fp)

            metadata = (content.get("metadata", {})
                               .get("AYON_NODE_METADATA", []))
            final_metadata = []
            for item in metadata:
                if item["id"] != AVALON_CONTAINER_ID:
                    final_metadata.append(item)
                    continue
                if item["nodeId"] != nodeId:
                    final_metadata.append(item)
                    continue

                updated = self._update_placeholder_string(container,
                                                          representation)
                repre, filled_value = fill_placeholder(updated,
                                                       container["namespace"],
                                                       context)
                item["representation"] = repre["_id"]
                item["original_value"] = updated
                item["name"] = os.path.basename(filled_value)
                item["version"] = repre["context"]["version"]

                final_metadata.append(item)

                for node in content["nodes"].values():
                    if node["nodeId"] != nodeId:
                        continue
                    node["params"]["fileName"]["value"] = filled_value

        self._save_metadata(container["namespace"], content, final_metadata)

    def _update_placeholder_string(self, container, representation):
        orig_token_values = get_token_and_values(
            container["original_value"])
        orig_token_values["version"] = \
            str(representation["context"]["version"])
        orig_token_values["asset_name"] = \
            representation["context"]["asset"]
        orig_token_values["ext"] = representation["context"]["ext"]
        orig_token_values["product_name"] = representation["context"]["subset"]
        updated = ".".join(list(orig_token_values.values()))
        return updated

    def remove(self, container):
        """
            Removes element from scene: deletes layer + removes from Headline
        Args:
            container (dict): container to be removed - used to get layer_id
        """
        nodeId = container["nodeId"]
        with open(container["namespace"], "r") as fp:
            content = json.load(fp)

            metadata = (content.get("metadata", {})
                        .get("AYON_NODE_METADATA", []))
            final_metadata = []
            for item in metadata:
                if item["id"] != AVALON_CONTAINER_ID:
                    final_metadata.append(item)
                    continue
                if item["nodeId"] != nodeId:
                    final_metadata.append(item)
                    continue

        final_nodes = {}
        for node_name, node in content["nodes"].items():
            if node["nodeId"] == nodeId:
                node["params"]["fileName"]["value"] = ""

            final_nodes[node_name] = node
        content["nodes"] = final_nodes

        self._save_metadata(container["namespace"], content, final_metadata)

    def switch(self, container, representation):
        self.update(container, representation)

    def _save_metadata(self, workfile_path, content, final_metadata):
        content["metadata"]["AYON_NODE_METADATA"] = final_metadata
        with open(workfile_path, "w") as fp:
            json.dump(content, fp, indent=4)
