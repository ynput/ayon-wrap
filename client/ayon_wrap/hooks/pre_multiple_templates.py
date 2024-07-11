from ayon_applications import (
    PreLaunchHook,
    LaunchTypes,
)
from ayon_core.tools.utils import qt_app_context
from ayon_core.lib.profiles_filtering import filter_profiles

from ayon_wrap.workfiles import WorkfilesToolWindow


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
        context_data = self.launch_context.data
        task_entity = context_data["task_entity"]
        task_name = task_entity["name"]
        task_type = task_entity["taskType"]

        wrap_settings = context_data["project_settings"]["wrap"]
        multiple_templates_profiles = (
            wrap_settings)["multiple_templates_per_tasks"]["profiles"]
        if not multiple_templates_profiles:
            return

        found_profile = filter_profiles(
            multiple_templates_profiles,
            {
                "task_names": task_name,
                "task_types": task_type,
            },
            logger=self.log
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
            workfiles_tool.show()
            workfiles_tool.raise_()
            workfiles_tool.activateWindow()
            workfiles_tool.showNormal()

            workfiles_tool.exec_()
