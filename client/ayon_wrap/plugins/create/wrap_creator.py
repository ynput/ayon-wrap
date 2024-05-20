import copy
import os
import json

from ayon_core.lib import (
    FileDef,
)
from ayon_core.pipeline import (
    CreatedInstance,
)
from ayon_core.hosts.traypublisher.api.plugin import TrayPublishCreator


class WrapWorkfileCreator(TrayPublishCreator):
    identifier = "Wrap"
    product_type = "wrap"

    default_variant = "Main"
    extensions = ["wrap"]

    output_node_types = ["SaveGeom"]

    def get_instance_attr_defs(self):
        return []

    def create(
        self, product_name: str, instance_data: dict, pre_create_data: dict
    ):
        file_paths = pre_create_data.get("filepath")
        if not file_paths:
            return

        for file_info in file_paths:
            instance_data = copy.deepcopy(instance_data)
            file_name = file_info["filenames"][0]
            filepath = os.path.join(file_info["directory"], file_name)
            creator_attributes = {"workfile_path": filepath}

            with open(filepath, "r") as fp:
                content = json.load(fp)

                for node in content["nodes"].values():
                    if node["nodeType"] not in self.output_node_types:
                        continue

                    creator_attributes["nodeId"] = node["nodeId"]
                    creator_attributes["output_file_path"] = (node["params"]
                                                                  ["fileName"]
                                                                  ["value"])
                    instance_data["creator_attributes"] = creator_attributes

                    new_instance = CreatedInstance(
                        self.product_type,
                        product_name,
                        instance_data,
                        self
                    )
                    self._store_new_instance(new_instance)

    def get_pre_create_attr_defs(self):
        # Use same attributes as for instance attributes
        return [
            FileDef(
                "filepath",
                folders=False,
                single_item=False,
                extensions=self.extensions,
                allow_sequences=False,
                label="Filepath"
            )
        ]

    def get_detail_description(self):
        return """# Create instances from Wrap Save nodes
        
        Looks for node types configured in `self.output_node_types` and for 
        each of them it created an instance.
        """

    def get_icon(self):
        return "fa.file"
