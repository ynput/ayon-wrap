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
from ayon_traypublisher.api.plugin import (
    TrayPublishCreator,
    HiddenTrayPublishCreator
)


class WrapCreator(TrayPublishCreator):
    """"Parses Wrap workfile, looks for all writer nodes names starting `AYON_`

    Expected format of write node name:
        `AYON_productName_extension` - eg `AYON_modelMain_abc`

    Triggers separate creators inheriting from 'WrapProductBaseCreator' which
    provides different icons and separation into product_types blocks.
    """
    host_name = "traypublisher"
    identifier = "wrap"
    product_type = None
    label = "Wrap"

    default_variant = "Main"
    extensions = ["wrap"]

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

                    product_name = self._get_product_name(node_name)
                    product_type = self._get_product_type(
                        node_name, product_name)

                    wrap_instance_data["nodeId"] = node["nodeId"]
                    wrap_instance_data["nodeName"] = node_name
                    wrap_instance_data["output_file_path"] = (
                        node["params"]["fileName"]["value"])
                    instance_data["wrap"] = wrap_instance_data

                    creator_identifier = f"wrap_{product_type}"
                    wrap_creator = self.create_context.creators[
                        creator_identifier]
                    _new_instance = wrap_creator.create(
                        product_name,
                        instance_data,
                    )

    def _get_product_name(self, node_name):
        """Parses node name by '_'

        Raises:
            (CreatorError) - if name doesn't match expected format
        """
        node_parts = node_name.split("_")
        if len(node_parts) != 3:
            raise CreatorError(
                f"'{node_name} doesn't match to "
                "expected write node format "
                "'AYON_productName_extension'"
            )
        product_name = node_parts[1]
        return product_name

    def _get_product_type(self, node_name, product_name):
        """Queries product type from list of implemented

        Node name contains full product_name, which must be stripped to get
        product_type.

        Raises:
            (CreatorError) - if name doesn't match expected format
        """
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
        return product_type

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


class WrapProductBaseCreator(HiddenTrayPublishCreator):
    """Wrapper class for separate product types implemented from Wrap."""
    host_name = "traypublisher"

    def create(self, product_name, instance_data):

        # Create new instance
        new_instance = CreatedInstance(
            self.product_type, product_name, instance_data, self
        )
        new_instance.data["families"] = ["wrap"]

        self._store_new_instance(new_instance)

        return new_instance


class ModelWrapCreator(WrapProductBaseCreator):
    identifier = "wrap_model"
    product_type = "model"
    label = "Wrap model"
    icon = "cube"


class DataTransformWrapCreator(WrapProductBaseCreator):
    identifier = "wrap_dataTransform"
    product_type = "dataTransform"
    label = "Wrap dataTransform"
    icon = "shuffle"


class DataPDWrapCreator(WrapProductBaseCreator):
    identifier = "wrap_dataPD"
    product_type = "dataPD"
    label = "Wrap dataPD"
    icon = "calendar-week"


class RenderCreator(WrapProductBaseCreator):
    identifier = "wrap_render"
    product_type = "render"
    label = "Wrap render"
    icon = "eye"


class ImageCreator(WrapProductBaseCreator):
    identifier = "wrap_image"
    product_type = "image"
    label = "Wrap image"
    icon = "image"
