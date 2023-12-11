import collections

from openpype.lib import ApplicationLaunchFailed
from openpype.client import (
    get_subset_by_name,
    get_last_versions,
    get_version_by_name,
    get_representations,
    get_hero_version_by_subset_id,
    get_asset_by_name
)
from openpype.pipeline import Anatomy
from openpype.pipeline.load import get_representation_path_with_anatomy

# expected pattern of placeholder value
PLACEHOLDER_VALUE_PATTERN = "AYON.asset_name.product_name.version.ext"


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

    asset_name = token_and_values["asset_name"]
    asset = _get_asset(project_name, asset_name, context)
    asset_id = asset["_id"]

    product_name = token_and_values["product_name"]
    product_id = _get_product_id(project_name,
                                 asset_id,
                                 product_name,
                                 asset["name"])

    version_val = token_and_values["version"]
    version_id = _get_version(project_name, product_name, product_id,
                              version_val, workfile_path)

    ext = token_and_values["ext"]
    repre, repre_path = _get_repre_and_path(project_name,
                                            product_name,
                                            ext, version_id)

    return repre, repre_path


def get_token_and_values(placeholder):
    return dict(zip(PLACEHOLDER_VALUE_PATTERN.split("."),
                    placeholder.split(".")))


def _get_repre_and_path(project_name, product_name, ext, version_id):
    repres = get_representations(project_name, version_ids=[version_id],
                                 representation_names=[ext])
    if not repres:
        raise ApplicationLaunchFailed(f"Cannot find representations with "
                                      f"'{ext}' for product '{product_name}'.\n"  # noqa
                                      f"Cannot import them.")
    repre = list(repres)[0]

    return repre, get_representation_path_with_anatomy(repre,
                                                       Anatomy(project_name))


def _get_version(project_name, product_name, product_id,
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
            raise ApplicationLaunchFailed(
                f"Couldn't convert value '{version_val}' to "
                f"integer. Please fix it in '{workfile_path}'")
        version_doc = get_version_by_name(project_name, version_int,
                                          product_id)
    if not version_doc:
        raise ApplicationLaunchFailed(f"Didn't find version "
                                      f"for product '{product_name}.\n")
    version_id = version_doc["_id"]
    return version_id


def _get_asset(project_name, asset_name, context):
    if asset_name == "{currentAsset}":
        if context.get("asset_doc"):
            return context["asset_doc"]
        asset_name = context["asset_name"]

    asset = get_asset_by_name(project_name, asset_name)
    if not asset:
        raise ApplicationLaunchFailed(f"Couldn't find '{asset_name}' in "
                                      f"'{project_name}'")

    return asset


def _get_product_id(project_name, asset_id, product_name, asset_name):
    product = get_subset_by_name(
        project_name, product_name, asset_id, fields=["_id"]
    )
    if not product:
        raise ApplicationLaunchFailed(f"Couldn't find '{product_name}' for "
                                      f"'{asset_name}'")
    product_id = product["_id"]
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
