from pydantic import Field
from ayon_server.settings import BaseSettingsModel
from .workfile_builder import WorkfileBuilderPlugin
from .multiple_templates import MultipleTemplatesModel


class WrapSettings(BaseSettingsModel):
    """Wrap Project Settings."""

    workfile_builder: WorkfileBuilderPlugin = Field(
        default_factory=WorkfileBuilderPlugin,
        title="Workfile Builder"
    )

    multiple_templates_per_tasks:  MultipleTemplatesModel = Field(
        default_factory=MultipleTemplatesModel,
        title="Multiple templates per task",
        description="Configure paths for multiple templates for single task. "
                    "Artist will be shown dialog to choose from templates."
    )


DEFAULT_WRAP_SETTING = {
  "workfile_builder": {
    "create_first_version": False,
  },
  "multiple_templates_per_tasks": {
    "profiles": []
  }
}
