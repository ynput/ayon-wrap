import platform
import os

import ayon_api
from qtpy import QtWidgets

from ayon_core.lib.events import QueuedEventSystem

from ayon_core.pipeline import Anatomy
from ayon_core.settings import get_project_settings
from ayon_core.pipeline.template_data import (
    get_template_data,
)

from ayon_wrap.api.lib import get_multiple_templates_profile
from ayon_wrap.workfiles.abstract import FileItem


class WorkfileToolController:
    """This is a temporary controller for AYON.

    Goal of this controller is to provide a way to get current context.
    """

    def __init__(self, launch_data):
        project_name = launch_data["project_name"]
        folder_id = launch_data["folder_id"]
        task_id = launch_data["task_id"]

        folder_entity = ayon_api.get_folder_by_id(project_name, folder_id)
        if not folder_entity:
            raise RuntimeError(f"Couldn't find folder for {folder_id}")
        self._current_folder_entity = folder_entity

        task_entity = ayon_api.get_task_by_id(project_name, task_id)
        if not task_entity:
            raise RuntimeError(f"Couldn't find task for {task_id}")
        self._current_task_entity = task_entity

        self._current_project_name = project_name
        self._current_folder_id = folder_id
        self._current_task_id = task_id

        self._project_settings = get_project_settings(
            self._current_project_name)
        self._anatomy = Anatomy(self._current_project_name)

        self._event_system = self._create_event_system()

        self._workfile_info_cache = {}

    def reset(self):
        pass

    @property
    def current_project_name(self):
        return self._current_project_name

    @property
    def current_task_name(self):
        return self._current_task_entity["name"]

    @property
    def current_task_type(self):
        return self._current_task_entity["taskType"]

    @property
    def current_folder_id(self):
        return self._current_folder_id

    def emit_event(self, topic, data=None, source=None):
        if data is None:
            data = {}
        self._event_system.emit(topic, data, source)

    def register_event_callback(self, topic, callback):
        self._event_system.add_callback(topic, callback)

    def get_workfile_extensions(self):
        return [".wrap"]

    def get_host_name(self):
        return "wrap"

    def _create_event_system(self):
        return QueuedEventSystem()

    def get_workarea_file_items(self, template_name):
        items = []
        project_entity = ayon_api.get_project(self._current_project_name)
        template_data = get_template_data(
            project_entity,
            self._current_folder_entity,
            self._current_task_entity,
            self.get_host_name(),
            self._project_settings
        )
        template_data["root"] = self._anatomy.roots
        template_data["template_name"] = template_name

        template = (self._project_settings["wrap"]
                                          ["multiple_templates_per_tasks"]
                                          ["workfile_template"])

        directory_template = template["directory_template"]

        workdir = directory_template.format(**template_data)

        if not os.path.exists(workdir):
            return items

        for filename in os.listdir(workdir):
            filepath = os.path.join(workdir, filename)
            if not os.path.isfile(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.get_workfile_extensions():
                continue

            workfile_info = self._get_workfile_info(
                self._current_project_name,
                self._current_task_entity["id"],
                filepath
            )
            modified = os.path.getmtime(filepath)
            created_by = updated_by = None
            if workfile_info:
                created_by = workfile_info.created_by
                updated_by = workfile_info.updated_by
            items.append(FileItem(
                workdir,
                filename,
                modified,
                created_by,
                updated_by,
            ))
        return items

    def _get_workfile_info(
            self, project_name, task_id, workfile_path):
        """Get DB stored info about work workfile."""
        workfile_info = self._workfile_info_cache.get(workfile_path)
        if workfile_info is not None:
            return workfile_info

        for workfile_info in ayon_api.get_workfiles_info(
            project_name,
            task_ids=[task_id],
            fields=["id", "path", "attrib", "createdBy", "updatedBy"],
        ):

            self._workfile_info_cache[workfile_path] = workfile_info
        return self._workfile_info_cache.get(workfile_path)

    def fill_templates(self, templates_widget):
        task_name = self._current_task_entity["name"]
        task_type = self._current_task_entity["taskType"]
        templates = self._get_template_paths(
            self._project_settings, task_name, task_type)
        for template_name in templates.keys():
            QtWidgets.QListWidgetItem(template_name, templates_widget)

    def _get_template_paths(self, project_settings, task_name, task_type):
        """Returns dictionary of templates and its paths."""
        templates = {}

        profile = get_multiple_templates_profile(
            project_settings,
            task_name,
            task_type
        )
        current_platform = platform.system().lower()

        for template in profile["templates"]:
            template_path = template["path"][current_platform]
            templates[template["template_name"]] = template_path

        return templates
