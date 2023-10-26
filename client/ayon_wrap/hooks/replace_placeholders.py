import os
import shutil
import json
import re

from openpype.lib.applications import PreLaunchHook, LaunchTypes
from openpype.lib import ApplicationLaunchFailed
from openpype.client import (
    get_subset_by_name,
    get_last_versions,
    get_version_by_name,
    get_representations,
    get_hero_version_by_subset_id,
    get_asset_by_name
)

from openpype.pipeline.load import get_representation_path_with_anatomy
from openpype.pipeline import Anatomy


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
    # expected pattern of placeholder value
    PLACEHOLDER_VALUE_PATTERN = "AYON.asset_name.product_name.version.ext"

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

        Searches for PLACEHOLDER_PATTERN, tries to fill it with dynamic values
        and replaces it.
        """
        filled_value = None
        with open(workfile_path, "r") as f:
            content = json.load(f)
            for node in content["nodes"].values():
                if not node.get("params"):
                    continue
                file_path_doc = node["params"].get("fileName")
                if not file_path_doc:
                    continue

                placeholder = self._get_placeholder(file_path_doc)
                if not placeholder:
                    continue

                filled_value = self._fill_placeholder(placeholder,
                                                      workfile_path)
                node["params"]["fileName"]["value"] = filled_value
                metadata = (f"AYON_ORIGINAL = \"{placeholder}\" "
                            "  \"\"\" AYON METADATA please do not remove!! \"\"\"\n"  # noqa
                           f"return {json.dumps(filled_value, ensure_ascii=True)}")   # noqa
                node["params"]["fileName"]["expression"] = metadata

        if filled_value:
            backup_path = f"{workfile_path}.bck"
            shutil.copy(workfile_path, backup_path)

            with open(workfile_path, "w") as fp:
                json.dump(content, fp, indent=4)

            os.unlink(backup_path)

    def _get_placeholder(self, file_info):
        if file_info["value"].startswith("AYON"):
            return file_info["value"]
        expression = file_info.get("expression")
        if expression and "AYON_ORIGINAL" in expression:
            pattern = r"AYON_ORIGINAL = \"([^\"]+)\""
            match = re.search(pattern, expression)
            if match:
                return match.group(1)
        return None

    def _fill_placeholder(self, placeholder, workfile_path):
        """Replaces placeholder with actual path to representation

        Args:
            placeholder (str): in format self.PLACEHOLDER_VALUE_PATTERN
            workfile_path (str): absolute path to opened workfile
        Returns:
            (str) path to resolved representation file which should be used
                instead of placeholder
        Raises
            (ApplicationLaunchFailed) if path cannot be resolved (cannot find product,
                version etc.)

        """
        token_values = dict(zip(self.PLACEHOLDER_VALUE_PATTERN.split("."),
                                placeholder.split(".")))

        project_name = self.data["project_name"]

        asset_name = token_values["asset_name"]
        asset_id = self._get_asset_id(project_name, asset_name)

        product_name = token_values["product_name"]
        product_id = self._get_product_id(project_name, asset_id,
                                          product_name)

        version_val = token_values["version"]
        version_id = self._get_version(project_name, product_name, product_id,
                                       version_val, workfile_path)

        ext = token_values["ext"]
        repre_path = self._get_repre_path(project_name, product_name, ext,
                                          version_id)

        return repre_path

    def _get_repre_path(self, project_name, product_name, ext, version_id):
        repres = get_representations(project_name, version_ids=[version_id],
                                     representation_names=[ext])
        if not repres:
            raise ApplicationLaunchFailed(f"Cannot find representations with "
                             f"{ext} for product {product_name}.\n"
                             f"Cannot import them.")
        repre = list(repres)[0]

        return get_representation_path_with_anatomy(repre,
                                                    Anatomy(project_name))

    def _get_version(self, project_name, product_name, product_id,
                     version_val, workfile_path):
        if version_val == "{latest}":
            versions = get_last_versions(project_name, [product_id])
            version_doc = versions[product_id]
        elif version_val == "{hero}":
            version_doc = get_hero_version_by_subset_id(project_name,
                                                        product_id)
        else:
            try:
                version_int = int(version_val)
            except:
                raise ApplicationLaunchFailed(f"Couldn't convert value {version_val} to "
                                 f"integer. Please fix it in {workfile_path}")
            version_doc = get_version_by_name(project_name, version_int,
                                              product_id)
        if not version_doc:
            raise ApplicationLaunchFailed(f"Didn't find version "
                             f"for product {product_name}.\n")
        version_id = version_doc["_id"]
        return version_id

    def _get_asset_id(self, project_name, asset_name):
        asset_doc = self.data["asset_doc"]
        if asset_name == "{currentAsset}":
            return asset_doc["_id"]

        asset = get_asset_by_name(project_name, asset_name)
        if not asset:
            raise ApplicationLaunchFailed(f"Couldn't find {asset_name} in "
                                          f"{project_name}")

        return asset["_id"]

    def _get_product_id(self, project_name, asset_id, product_name):
        product = get_subset_by_name(
            project_name, product_name, asset_id, fields=["_id"]
        )
        if not product:
            raise ApplicationLaunchFailed(f"Couldn't find {product_name} for "
                             "{asset_doc[\"name\"]}")
        product_id = product["_id"]
        return product_id

