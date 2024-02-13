import pyblish.api
from openpype.lib.applications import ApplicationManager
from ayon_wrap.api.lib import find_variant_key


class CollectExtensionVersion(pyblish.api.ContextPlugin):
    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Executable Path"
    hosts = ["traypublisher"]

    optional = False
    active = True

    def process(self, context):
        host_name = "wrap"
        application_manager = ApplicationManager()
        found_variant_key = find_variant_key(application_manager, host_name)
        app_name = "{}/{}".format(host_name, found_variant_key)

        launch_context = application_manager.create_launch_context(
            app_name)
        context.data["wrapExecutablePath"] = launch_context.executable.executable_path  # noqa
