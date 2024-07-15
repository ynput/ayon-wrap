import platform
import os
import shutil

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
        self._current_template_name = None

        self._project_settings = get_project_settings(
            self._current_project_name)
        self._anatomy = Anatomy(self._current_project_name)

        self._templates = {}
        self._template_workdirs = {}

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

    @property
    def current_template_name(self):
        return self._current_template_name

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
        workdir = self._template_workdirs.get(template_name)
        if not workdir:
            workdir = self._get_workdir(template_name)
            self._template_workdirs[template_name] = workdir

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

    def _get_workdir(self, template_name):
        """Calculates workdir for template_name"""
        template_data = self._get_template_data(template_name)
        template = (
            self._project_settings["wrap"]
            ["multiple_templates_per_tasks"]
            ["workfile_template"]
        )
        directory_template = template["directory_template"]

        workdir = directory_template.format(**template_data)
        return workdir

    def _get_first_workfile_name(self, template_name):
        template_data = self._get_template_data(template_name)
        template_data["@version"] = "v001"
        template_data["comment"] = ""
        template_data["ext"] = (self.get_workfile_extensions()[0]
                                    .replace(".", ""))
        template = (
            self._project_settings["wrap"]
            ["multiple_templates_per_tasks"]
            ["workfile_template"]
        )
        filename_template = template["filename_template"]

        work_filename = filename_template.format(**template_data)
        return work_filename


    def _get_template_data(self, template_name):
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
        return template_data

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
        """Adds template names into templates_widget"""
        task_name = self._current_task_entity["name"]
        task_type = self._current_task_entity["taskType"]
        templates = self._get_template_paths(
            self._project_settings, task_name, task_type)
        for template_name in templates.keys():
            QtWidgets.QListWidgetItem(template_name, templates_widget)

        self._templates = templates

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

    def open_workfile(self, path):
        os.environ["WRAP_WORKFILE_PATH"] = path

    def create_new_workfile(self):
        """Copies template to workarea"""
        if not self.current_template_name:
            raise RuntimeError("No template chosen yet!")

        if not self._templates:
            raise RuntimeError("No templates found!")

        template_path = self._templates[self.current_template_name]

        workdir = self._template_workdirs.get(self.current_template_name)
        if not workdir:
            raise RuntimeError("Not workfile found for "
                               f"{self.current_template_name}")

        work_filename = self._get_first_workfile_name(
            self.current_template_name)

        if not os.path.exists(workdir):
            os.makedirs(workdir, exist_ok=True)
        first_workfile_path = os.path.join(workdir, work_filename)
        shutil.copy(template_path, first_workfile_path)

        os.environ["WRAP_WORKFILE_PATH"] = first_workfile_path
