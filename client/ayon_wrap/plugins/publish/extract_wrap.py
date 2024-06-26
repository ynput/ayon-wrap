import os
import subprocess
import json

from ayon_core.pipeline import publish


class ExtractCompute(publish.Extractor):
    """Render RenderQueue locally."""

    order = publish.Extractor.order - 0.47
    label = "Extract Compute Nodes"
    hosts = ["traypublisher"]
    families = ["wrap"]

    def process(self, instance):
        workfile_path = instance.data["wrap"]["workfile_path"]

        output_file_path = instance.data["wrap"]["output_file_path"]
        is_absolute = os.path.isabs(output_file_path)
        if is_absolute:
            staging_dir = os.path.dirname(output_file_path)
        else:
            output_file_path = os.path.join(
                os.path.dirname(workfile_path), output_file_path)
            staging_dir = os.path.dirname(output_file_path)

        representations = []
        _, ext = os.path.splitext(os.path.basename(output_file_path))
        ext = ext[1:]

        asset_doc = instance.data["assetEntity"]
        frame_start = asset_doc["data"]["frameStart"]
        frame_end = asset_doc["data"]["frameEnd"]

        self._update_timeline(workfile_path, frame_start, frame_end)

        exit_code = self._call_compute(workfile_path, instance,
                                       frame_start, frame_end)

        if exit_code != 0:
            raise RuntimeError(f"Cannot compute {workfile_path}")

        files = []
        for found_file_name in os.listdir(staging_dir):
            if not found_file_name.endswith(ext):
                continue

            files.append(found_file_name)

        if len(files) == 1:
            files = files[0]

        repre_data = {
            "frameStart": frame_start,
            "frameEnd": frame_end,
            "name": ext,
            "ext": ext,
            "files": files,
            "stagingDir": staging_dir
        }

        representations.append(repre_data)

        instance.data["representations"] = representations

        instance.context.data["currentFile"] = workfile_path  # TODO

    def _update_timeline(self, workfile_path, frame_start, frame_end):
        """Frame_start and frame_end must be inside of timeline values."""
        with open(workfile_path, "r") as fp:
            content = json.load(fp)

        content["timeline"]["min"] = frame_start
        content["timeline"]["current"] = frame_start
        content["timeline"]["max"] = frame_end

        with open(workfile_path, "w") as fp:
            json.dump(content, fp, indent=4)

    def _call_compute(self, workfile_path, instance, frame_start, frame_end):
        """Trigger compute on workfile"""
        wrap_executable_path = instance.context.data["wrapExecutablePath"]
        wrap_executable_path = wrap_executable_path.replace("Wrap.",
                                                            "WrapCmd.")
        subprocess_args = [wrap_executable_path, "compute", workfile_path,
                           "-s", str(frame_start),
                           "-e", str(frame_end)]
        self.log.debug(f"args::{subprocess_args}")
        exit_code = subprocess.call(subprocess_args,
                                    cwd=os.path.dirname(workfile_path))
        return exit_code
