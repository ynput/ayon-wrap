import os
import shutil
import json

from ayon_applications import PreLaunchHook, LaunchTypes
from ayon_core.pipeline import Anatomy, AVALON_CONTAINER_ID
from ayon_core.lib import get_version_from_path

from ayon_wrap import api


class ReplacePlaceholders(PreLaunchHook):
    """Search and replace placeholders for path and replace them from Ayon

    It updates copied variant of template workfile if first version of workfile
    doesn't exist, it modifies last opened workfile if exists (TODO).
    Some read and write nodes might contain text Ayon placeholders describing
    what product, version and representation should be loaded.

    Expected placeholder format is PLACEHOLDER_VALUE_PATTERN.
    Implemented 'placeholder' in 'placeholder':
        - asset_name - {currentAsset} or any asset_name
        - version - {latest} or {hero} or any integer value
        (AYON.{currentAsset}.modelMain.{latest}.abc
         AYON.characterB.modelMain.{hero}.abc
         AYON.{currentAsset}.modelMaoin.1.abc)
    """

    order = 25
    app_groups = {"wrap"}
    launch_types = {LaunchTypes.local}

    PLACEHOLDER_PATTERN = "\"value\": \"^AYON\.\".*$"

    def execute(self):
        last_workfile_path = self.data.get("last_workfile_path")
        if not last_workfile_path or not os.path.exists(last_workfile_path):
            self.log.warning((
                "Last workfile was not collected."
                " No placeholder replacement is possible."
            ))
            return

        self._fill_placeholders(last_workfile_path)

        self.log.info(f"Updating: \"{last_workfile_path}\"")

    def _fill_placeholders(self, workfile_path):
        """Replaces placeholders in existing `workfile_path`.

        Args:
            workfile_path (str): real workfile in 'work' area that will be
                opened, already copied from template

        Searches for PLACEHOLDER_PATTERN, tries to fill it with dynamic values
        and replaces it.
        """
        with open(workfile_path, "r") as f:
            content = json.load(f)

            orig_metadata = (content.get("metadata", {})
                                    .get("AYON_NODE_METADATA", {}))

            containers = []
            stored_containers = {item["nodeId"]: item
                                 for item in orig_metadata
                                 if item.get("nodeId") is not None}
            for node_name, node in content["nodes"].items():
                load_placeholder = self._get_load_placeholder(
                    node, stored_containers)
                if load_placeholder:
                    containers.append(
                        self._containerize_load_placeholder(node,
                                                            node_name,
                                                            load_placeholder,
                                                            workfile_path)
                    )

                if node_name.startswith("AYON_"):  #TODO
                    file_path = node["params"]["fileName"]["value"]
                    workfile_version = f"v{get_version_from_path(workfile_path)}"  # noqa

                    file_path = self._update_version_placeholder(
                        workfile_version, file_path)

                    node["params"]["fileName"]["value"] = file_path

            # keep untouched meta
            for existing_node_meta in orig_metadata:
                if existing_node_meta["id"] != AVALON_CONTAINER_ID:
                    containers.append(existing_node_meta)

            if not containers and not orig_metadata:
                return

            if not content.get("metadata"):
                content["metadata"] = {}
            content["metadata"]["AYON_NODE_METADATA"] = containers

            backup_path = f"{workfile_path}.bck"
            shutil.copy(workfile_path, backup_path)

            with open(workfile_path, "w") as fp:
                json.dump(content, fp, indent=4)

            os.unlink(backup_path)

    def _update_version_placeholder(self, workfile_version, file_path):
        """Searches for {version} or 'v000' placeholder in output file path"""
        if "{version}" in file_path:
            file_path = file_path.replace("{version}",
                                          workfile_version)
        else:
            version_from_path = get_version_from_path(file_path)
            if version_from_path:
                file_path = file_path.replace(version_from_path,
                                              workfile_version)

        return file_path

    def _get_load_placeholder(self, node, stored_containers):
        """Checks if node contains placeholder for loaded items.

        It might be directly in file path of the node (for fresh template), or
        resolved and saved in `stored_containers`.
        Args:
            node (dict): dictionary of node from Wrap file
            stored_containers (dict): id -> container metadata for resolved
                and saved loaded container.
        Returns:
            (str): placeholder in format `AYON.{currentAsset}.renderMain...`
        """
        if not node.get("params"):
            return None
        file_path_doc = node["params"].get("fileName")
        if not file_path_doc:
            return None

        stored_node_meta = stored_containers.get(node["nodeId"])
        return self._get_placeholder(file_path_doc, stored_node_meta)

    def _containerize_load_placeholder(self, node, node_name,
                                       placeholder, workfile_path):
        """Resolves string placeholder with actual path to product.

        Args:
            node (dict): node dictionary from Wrap
            node_name (str):
            placeholder (str): placeholder in format
                `AYON.{currentAsset}.renderMain...`
            workfile_path (str): abs path to workfile to store into metadata
        Returns:
            (dict): AYON container metadata
        """
        repre, filled_value = api.fill_placeholder(placeholder,
                                                   workfile_path,
                                                   self.data)
        node["params"]["fileName"]["value"] = filled_value
        data = {
            "original_value": placeholder,
            "nodeId": node["nodeId"],
            "node_name": node_name
        }
        context = self.data
        context["representation"] = repre

        return api.containerise(
            name=os.path.basename(filled_value),
            namespace=workfile_path,
            loader="FileLoader",
            context=context,
            data=data
        )

    def _get_placeholder(self, file_info, stored_node_meta):
        """Gets placeholder from file path of node or stored metadata.

        Node filepath has precedence as it could be changed by artist,
        metadata might contain obsolete value.
        """
        if file_info["value"].startswith("AYON"):
            return file_info["value"]
        if stored_node_meta and stored_node_meta["id"] == AVALON_CONTAINER_ID:
            return stored_node_meta["original_value"]
