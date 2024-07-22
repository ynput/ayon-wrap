import os.path

from ayon_applications import (
    PreLaunchHook,
    LaunchTypes,
)
from ayon_core.tools.utils import qt_app_context

from ayon_wrap.api.lib import get_multiple_templates_profile


class PreLaunchMultipleTemplatesHook(PreLaunchHook):
    """Launch dialog to select from multiple templates for current task

    Uses profiles to check if current context should offer artist selection
    from multiple templates.

    It overrides usage of generic template from Workfile builder configuration.

    """
    app_groups = {"wrap"}

    order = 10
    launch_types = {LaunchTypes.local}

    def execute(self):
        from ayon_wrap.workfiles.widgets import WorkfilesToolWindow

        context_data = self.launch_context.data
        task_entity = context_data["task_entity"]
        task_name = task_entity["name"]
        task_type = task_entity["taskType"]

        found_profile = get_multiple_templates_profile(
            context_data["project_settings"], task_name, task_type, self.log
        )

        if not found_profile:
            return

        project_name = context_data["project_name"]
        folder_entity = context_data["folder_entity"]
        with qt_app_context():
            launch_data = {
                "project_name": project_name,
                "folder_id": folder_entity["id"],
                "task_id": task_entity["id"]
            }
            workfiles_tool = WorkfilesToolWindow(launch_data=launch_data)
            workfiles_tool.exec_()
            workfile_path = os.environ.get("WRAP_WORKFILE_PATH")
            if not workfile_path or not os.path.exists(workfile_path):
                raise ApplicationLaunchFailed(f"'{workfile_path} doesn't exist!")
            workfile_path = os.path.normpath(workfile_path)
            self.log.debug(f"Opening {workfile_path} from multiple templates")
            self.data["last_workfile_path"] = os.path.normpath(workfile_path)
            self.launch_context.launch_args.pop(-1)
            self.launch_context.launch_args.append(workfile_path)
