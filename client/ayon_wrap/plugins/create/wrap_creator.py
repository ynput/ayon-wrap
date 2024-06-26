import copy
import os
import json

from ayon_core.lib import (
    FileDef,
)
from ayon_core.pipeline import (
    CreatedInstance,
    CreatorError
)
from ayon_traypublisher.api.plugin import TrayPublishCreator


class WrapWorkfileCreator(TrayPublishCreator):
    """"Parses Wrap workfile, looks for all writer nodes names starting `AYON_`

    Expected format of write node name:
        `AYON_productName_extension` - eg `AYON_modelMain_abc`
    """
    identifier = "Wrap"

    default_variant = "Main"
    extensions = ["wrap"]

    product_type = None

    implemented_product_types = [
        "model", "dataTransform", "dataPD", "render", "image"
    ]

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
            wrap_instance_data = {"workfile_path": filepath}
            with open(filepath, "r") as fp:
                content = json.load(fp)

                for node_name, node in content["nodes"].items():
                    if not node_name.startswith("AYON_"):
                        continue

                    node_parts = node_name.split("_")
                    if len(node_parts) != 3:
                        raise CreatorError(
                            f"'{node_name} doesn't match to "
                            "expected write node format "
                            "'AYON_productName_extension'"
                        )
                    product_name = node_parts[1]
                    product_type = None
                    for impl_product_type in self.implemented_product_types:
                        if product_name.startswith(impl_product_type):
                            product_type = impl_product_type
                            break
                    if not product_type:
                        raise CreatorError(
                            f"'{node_name} doesn't match to values from "
                            f"'{self.implemented_product_types}'"
                        )

                    wrap_instance_data["nodeId"] = node["nodeId"]
                    wrap_instance_data["nodeName"] = node_name
                    wrap_instance_data["output_file_path"] = (
                        node["params"]["fileName"]["value"])
                    instance_data["wrap"] = wrap_instance_data

                    new_instance = CreatedInstance(
                        product_type,
                        product_name,
                        instance_data,
                        self
                    )
                    self._store_new_instance(new_instance)

    def get_instance_attr_defs(self):
        return [
            FileDef(
                "filepath",
                folders=False,
                single_item=False,
                extensions=self.extensions,
                allow_sequences=False,
                label="Filepath",
                hidden=True
            )
        ]

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
        
        Looks for writer nodes with names starting by `AYON_`. Tries to match
        them to final 'product_type' by values in 
        `self.implemented_product_types`. 
        
        Eg. 'AYON_modelMain_abc' name produces instance of 'model' family with
        'renderMain' product name.
        """

    def get_icon(self):
        return "fa.file"
