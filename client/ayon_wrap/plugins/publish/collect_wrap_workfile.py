import os
import pyblish.api

from ayon_wrap.api.plugin import is_wrap_instance


class CollectWrapWorkfile(pyblish.api.InstancePlugin):
    """Collect current workfile for publish."""

    order = pyblish.api.CollectorOrder + 0.2
    label = "Collect Wrap Workfile"
    hosts = ["traypublisher"]

    families = ["workfile"]

    def process(self, instance):
        is_wrap = is_wrap_instance(instance, self.log)
        if not is_wrap:
            return

        workfile_path = instance.data["wrap"]["workfile_path"]
        workfile_name = os.path.basename(workfile_path)
        staging_dir = os.path.dirname(workfile_path)
        _, ext = os.path.splitext(workfile_name)
        workfile_representation = {
            "name": ext[1:],
            "ext": ext[1:],
            "files": workfile_name,
            "stagingDir": staging_dir,
        }

        instance.data["representations"].append(workfile_representation)
