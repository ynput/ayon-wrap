import os
import subprocess
import json

import pyblish

from ayon_core.pipeline import publish
from ayon_core.pipeline.publish import get_instance_staging_dir

from ayon_wrap.api.plugin import is_wrap_instance


class ExtractCompute(pyblish.api.ContextPlugin):
    """Render RenderQueue locally."""

    order = publish.Extractor.order - 0.47
    label = "Extract Compute Nodes"
    hosts = ["traypublisher"]
    families = ["wrap"]

    def process(self, context):
        node_id_to_output_path = {}
        output_path_to_instance = {}
        for instance in context:
            is_wrap = is_wrap_instance(instance, self.log)
            if not is_wrap:
                return

            workfile_path = instance.data["wrap"]["workfile_path"]
            workfile_dir = os.path.dirname(workfile_path)
            output_path = self._get_output_path(instance, workfile_dir)

            if output_path in output_path_to_instance:
                raise RuntimeError(f"{output_path} not unique!")
            output_path_to_instance[output_path] = instance

            node_id = instance.data["wrap"]["nodeId"]
            node_id_to_output_path[node_id] = output_path

        # same folderEntity for all instances
        folder_entity = instance.data["folderEntity"]
        frame_start = folder_entity["attrib"]["frameStart"]
        frame_end = folder_entity["attrib"]["frameEnd"]

        self._update_timeline(workfile_path, frame_start, frame_end)

        self._update_output_dirs(workfile_path, node_id_to_output_path)

        wrap_executable_path = instance.context.data["wrapExecutablePath"]
        exit_code = self._call_compute(
            workfile_path, wrap_executable_path, frame_start, frame_end)

        if exit_code != 0:
            raise RuntimeError(f"Cannot compute {workfile_path}")

        product_name_to_instance = {}
        for output_path, instance in output_path_to_instance.items():
            product_name = instance.data["productName"]
            another_instance = product_name_to_instance.get(product_name)

            _, ext = os.path.splitext(os.path.basename(output_path))
            ext = ext[1:]
            
            files = []
            output_dir = os.path.dirname(output_path)
            for found_file_name in os.listdir(output_dir):
                if not found_file_name.endswith(ext):
                    continue
    
                files.append(found_file_name)
                file_path = os.path.join(output_dir, found_file_name)
                instance.context.data["cleanupFullPaths"].append(file_path)
    
            if len(files) == 1:
                files = files[0]
    
            repre_data = {
                "frameStart": frame_start,
                "frameEnd": frame_end,
                "name": ext,
                "ext": ext,
                "files": files,
                "stagingDir": output_dir
            }

            if another_instance is not None:
                representations = another_instance.data.get(
                    "representations", [])
                instance = another_instance  # update existing instance
            else:
                representations = instance.data.get("representations", [])
                product_name_to_instance[product_name] = instance

            representations.append(repre_data)
            instance.data["representations"] = representations

        instance.context.data["currentFile"] = workfile_path  # TODO

    def _get_output_path(self, instance, workfile_dir):
        """Get output dir where writer node will save.

        If Wrap $PROJECT_DIR is not used, temporary folder will be created.
        Returns:
            [str]: full absolute path for writer node
        """
        output_file_path = instance.data["wrap"]["output_file_path"]
        output_file_name = os.path.basename(output_file_path)
        if "$PROJECT_DIR" in output_file_path:
            staging_dir = output_file_path.replace(
                "$PROJECT_DIR", workfile_dir)
        else:
            staging_dir = self.staging_dir(instance)
        output_path = os.path.join(staging_dir, output_file_name)
        return output_path

    def staging_dir(self, instance):
        """Provide a temporary directory in which to store extracted files

        Upon calling this method the staging directory is stored inside
        the instance.data['stagingDir']
        """

        return get_instance_staging_dir(instance)

    def _update_timeline(self, workfile_path, frame_start, frame_end):
        """Frame_start and frame_end must be inside of timeline values."""
        with open(workfile_path, "r") as fp:
            content = json.load(fp)

        content["timeline"]["min"] = frame_start
        content["timeline"]["current"] = frame_start
        content["timeline"]["max"] = frame_end

        with open(workfile_path, "w") as fp:
            json.dump(content, fp, indent=4)

    def _update_output_dirs(self, workfile_path, node_id_to_output_path):
        """Update all AYON_ writer nodes with path.

        Could be in same directory where workfile is, or in temporary folders.
        TODO revisit performance on separate parsing and writing to json,
        it is expected to be negligent
        """
        with open(workfile_path, "r") as fp:
            content = json.load(fp)

        for node in content["nodes"].values():
            node_id = node["nodeId"]
            output_dir = node_id_to_output_path.get(node_id)
            if not output_dir:
                continue
                
            node["params"]["fileName"]["value"] = output_dir

        with open(workfile_path, "w") as fp:
            json.dump(content, fp, indent=4)

    def _call_compute(
            self, workfile_path, wrap_executable_path, frame_start, frame_end):
        """Trigger compute on workfile"""
        wrap_executable_path = wrap_executable_path.replace("Wrap.",
                                                            "WrapCmd.")
        subprocess_args = [wrap_executable_path, "compute", workfile_path,
                           "-s", str(frame_start),
                           "-e", str(frame_end)]
        self.log.debug(f"args::{subprocess_args}")
        exit_code = subprocess.call(subprocess_args,
                                    cwd=os.path.dirname(workfile_path))
        return exit_code
