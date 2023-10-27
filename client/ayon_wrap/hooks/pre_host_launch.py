import os

from openpype.lib import get_openpype_execute_args
from openpype.lib.applications import (
    get_non_python_host_kwargs,
    PreLaunchHook,
    LaunchTypes,
)

WRAP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class PreLaunchHostHook(PreLaunchHook):
    """Launch arguments preparation.

    Non python host implementation do not launch host directly but use
    python script which launch the host. For these cases it is necessary to
    prepend python (or openpype) executable and script path before application's.
    """
    app_groups = {"wrap"}

    order = 20
    launch_types = {LaunchTypes.local}

    def execute(self):
        # Pop executable
        executable_path = self.launch_context.launch_args.pop(0)

        # Pop rest of launch arguments - There should not be other arguments!
        remainders = []
        while self.launch_context.launch_args:
            remainders.append(self.launch_context.launch_args.pop(0))

        script_path = os.path.join(
            WRAP_DIR,
            "api",
            "launch_logic.py"
        )

        new_launch_args = get_openpype_execute_args(
            "run", script_path, executable_path
        )
        # Add workfile path if exists
        workfile_path = self.data["last_workfile_path"]
        if (
                self.data.get("start_last_workfile")
                and workfile_path
                and os.path.exists(workfile_path)):
            new_launch_args.append(workfile_path)

        # Append as whole list as these areguments should not be separated
        self.launch_context.launch_args.append(new_launch_args)

        if remainders:
            self.launch_context.launch_args.extend(remainders)

        self.launch_context.kwargs = \
            get_non_python_host_kwargs(self.launch_context.kwargs)
