import collections

from ayon_applications import ApplicationLaunchFailed
from ayon_api import (
    get_folder_by_path,
    get_last_versions,
    get_version_by_name,
    get_representations,
    get_hero_version_by_product_id,
    get_product_by_name
)
from ayon_core.pipeline import Anatomy
from ayon_core.pipeline.load import get_representation_path_with_anatomy

# expected pattern of placeholder value
PLACEHOLDER_VALUE_PATTERN = "AYON.folder_token.product_name.version.ext"


def fill_placeholder(placeholder, workfile_path, context):
    """Replaces placeholder with actual path to representation

    Args:
        placeholder (str): in format PLACEHOLDER_VALUE_PATTERN
        workfile_path (str): absolute path to opened workfile
        context (dict): contains context data from launch context
    Returns:
        (dict, str) path to resolved representation file which should be used
            instead of placeholder
    Raises
        (ApplicationLaunchFailed) if path cannot be resolved (cannot find
        product, version etc.)

    """
    token_and_values = get_token_and_values(placeholder)

    project_name = context["project_name"]

    folder_token = token_and_values["folder_token"]
    folder_entity = _get_folder_entity(project_name, folder_token, context)
    folder_id = folder_entity["id"]

    product_name = token_and_values["product_name"]
    product_id = _get_product_id(
        project_name,
        folder_id,
        product_name,
        folder_entity["name"]
    )

    version_val = token_and_values["version"]
    version_id = _get_version(
        project_name,
        product_name,
        product_id,
        version_val,
        workfile_path
    )

    ext = token_and_values["ext"]
    repre, repre_path = _get_repre_and_path(
        project_name, product_name, ext, version_id)

    return repre, repre_path


def get_token_and_values(placeholder):
    return dict(zip(PLACEHOLDER_VALUE_PATTERN.split("."),
                    placeholder.split(".")))


def _get_repre_and_path(project_name, product_name, ext, version_id):
    repres = list(get_representations(
        project_name,
        version_ids=[version_id],
        representation_names=[ext]
    ))
    if not repres:
        raise ApplicationLaunchFailed(
            f"Cannot find representations with "
            f"'{ext}' for product '{product_name}'.\n"
            f"Cannot import them."
    )
    repre = repres[0]

    return repre, get_representation_path_with_anatomy(
        repre, Anatomy(project_name))


def _get_version(project_name, product_name, product_id,
                 version_val, workfile_path):
    if version_val == "{latest}":
        versions = get_last_versions(project_name, [product_id])
        version_doc = versions[product_id]
    elif version_val == "{hero}":
        version_doc = get_hero_version_by_product_id(
            project_name, product_id)
    else:
        try:
            version_int = int(version_val)
        except:
            raise ApplicationLaunchFailed(
                f"Couldn't convert value '{version_val}' to "
                f"integer. Please fix it in '{workfile_path}'")
        version_doc = get_version_by_name(
            project_name, version_int, product_id)
    if not version_doc:
        raise ApplicationLaunchFailed(f"Didn't find version "
                                      f"for product '{product_name}.\n")
    version_id = version_doc["id"]
    return version_id


def _get_folder_entity(project_name, folder_token, context):
    if folder_token == "{currentFolder}":
        return context["folder_entity"]

    folder_path = context["folder_path"]
    folder_entity = get_folder_by_path(project_name, folder_path)
    if not folder_entity:
        raise ApplicationLaunchFailed(f"Couldn't find '{folder_token}' in "
                                      f"'{project_name}'")

    return folder_entity


def _get_product_id(project_name, asset_id, product_name, asset_name):
    product_ent = get_product_by_name(
        project_name, product_name, asset_id
    )
    if not product_ent:
        raise ApplicationLaunchFailed(f"Couldn't find '{product_name}' for "
                                      f"'{asset_name}'")
    product_id = product_ent["id"]
    return product_id


def find_variant_key(application_manager, host):
    """Searches for latest installed variant for 'host'

        Args:
            application_manager (ApplicationManager)
            host (str)
        Returns
            (string) (optional)
        Raises:
            (ValueError) if no variant found
    """
    app_group = application_manager.app_groups.get(host)
    if not app_group or not app_group.enabled:
        raise ValueError("No application '{}' configured".format(host))

    found_variant_key = None
    # finds most up-to-date variant if any installed
    sorted_variants = collections.OrderedDict(
        sorted(app_group.variants.items()))
    for variant_key, variant in sorted_variants.items():
        for executable in variant.executables:
            if executable.exists():
                found_variant_key = variant_key

    if not found_variant_key:
        raise ValueError("No executable for '{}' found".format(host))

    return found_variant_key
