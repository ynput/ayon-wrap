import os
import platform
import shutil
import copy

import ayon_api

from ayon_core.lib.events import QueuedEventSystem
from ayon_core.settings import get_project_settings
from ayon_core.pipeline import Anatomy
from ayon_core.pipeline.version_start import get_versioning_start
from ayon_core.pipeline.template_data import get_template_data

from ayon_wrap.api.lib import get_multiple_templates_profile

from .abstract import FileItem


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

        task_entity = ayon_api.get_task_by_id(project_name, task_id)
        if not task_entity:
            raise RuntimeError(f"Couldn't find task for {task_id}")

        project_entity = ayon_api.get_project(project_name)

        # template name in Anatomy
        self.wrap_template_name = "wrap_multi"

        self._current_project_name = project_name
        self._current_folder_id = folder_id
        self._current_task_id = task_id
        self._current_template_name = None

        self._anatomy = None
        self._project_entity = project_entity
        self._task_entity = task_entity
        self._folder_entity = folder_entity

        self._project_settings = get_project_settings(project_name)

        self._templates = {}
        self._template_workdirs = {}

        self._event_system = self._create_event_system()

        self._workfile_info_cache = {}

    def reset(self):
        self._templates = self._get_template_paths(
            self._project_settings,
            self.current_task_name,
            self.current_task_type
        )
        self._anatomy = None

        self.emit_event("controller.reset.finished")

    @property
    def current_task_name(self):
        return self._task_entity["name"]

    @property
    def current_task_type(self):
        return self._task_entity["taskType"]

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

    def set_template(self, template_name):
        self._current_template_name = template_name
        data = {
            "template_name": template_name,
            "folder_id": self.current_folder_id,
            "task_name": self.current_task_name,
            "task_type": self.current_task_type,
        }
        self.emit_event(
            "template_changed",
            data=data
        )

    def get_workarea_file_items(self, template_name):
        workdir = self._template_workdirs.get(template_name)
        if workdir is None:
            workdir = self._get_workdir(template_name)
            self._template_workdirs[template_name] = workdir

        items = []
        if not os.path.exists(workdir):
            return items

        exts = self.get_workfile_extensions()
        for filename in os.listdir(workdir):
            filepath = os.path.join(workdir, filename)
            if not os.path.isfile(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in exts:
                continue

            workfile_info = self._get_workfile_info(
                self._current_project_name,
                self._current_task_id,
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

    def get_template_names(self):
        """Adds template names into templates_widget"""
        return list(self._templates.keys())

    def open_workfile(self, path):
        os.environ["WRAP_WORKFILE_PATH"] = path

    def create_new_workfile(self):
        """Copies template to workarea"""
        if not self._current_template_name:
            raise RuntimeError("No template chosen yet!")

        if not self._templates:
            raise RuntimeError("No templates found!")

        template_path = self._templates[self._current_template_name]

        workdir = self._template_workdirs.get(self._current_template_name)
        if not workdir:
            raise RuntimeError(
                f"Not workfile found for {self._current_template_name}"
            )

        work_filename = self._get_first_workfile_name(
            self._current_template_name)

        if not os.path.exists(workdir):
            os.makedirs(workdir, exist_ok=True)
        first_workfile_path = os.path.join(workdir, work_filename)
        shutil.copy(template_path, first_workfile_path)

        os.environ["WRAP_WORKFILE_PATH"] = first_workfile_path

    def _create_event_system(self):
        return QueuedEventSystem()

    def _get_current_anatomy(self):
        if self._anatomy is not None:
            return self._anatomy
        # Duplicate project so we can modify it
        project_entity = copy.deepcopy(self._project_entity)

        self._anatomy = Anatomy(
            self._current_project_name,
            project_entity=project_entity
        )
        return self._anatomy

    def _get_template_paths(self, project_settings, task_name, task_type):
        """Returns dictionary of templates and its paths."""
        templates = {}

        profile = get_multiple_templates_profile(
            project_settings,
            task_name,
            task_type
        )
        platform_name = platform.system().lower()
        for template in profile["templates"]:
            template_name = template["template_name"]
            templates[template_name] = template["path"][platform_name]

        return templates

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

    def _get_template_data(self, template_name):
        project_entity = ayon_api.get_project(self._current_project_name)
        template_data = get_template_data(
            project_entity,
            self._folder_entity,
            self._task_entity,
            self.get_host_name(),
            self._project_settings
        )
        anatomy = self._get_current_anatomy()
        template_data["root"] = anatomy.roots
        template_data["template_name"] = template_name
        return template_data

    def _get_workdir(self, template_name):
        """Calculates workdir for template_name"""
        template_data = self._get_template_data(template_name)
        anatomy = self._get_current_anatomy()
        template = anatomy.get_template_item(
            "work", self.wrap_template_name, "directory")
        return template.format(template_data)

    def _get_first_workfile_name(self, template_name):
        template_data = self._get_template_data(template_name)
        ext = self.get_workfile_extensions()[0].lstrip(".")
        version = get_versioning_start(
            self._current_project_name,
            self.get_host_name(),
            task_name=self.current_task_name,
            task_type=self.current_task_type,
            project_settings=self._project_settings
        )
        template_data["version"] = version
        template_data["comment"] = ""
        template_data["ext"] = ext

        anatomy = self._get_current_anatomy()
        template = anatomy.get_template_item(
            "work", self.wrap_template_name, "file")

        return template.format(template_data)
