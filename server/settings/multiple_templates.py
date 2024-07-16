from pydantic import Field

from ayon_server.settings import (
    BaseSettingsModel,
    MultiplatformPathModel,
    task_types_enum,
    SettingsField
)


class TemplatePathModel(BaseSettingsModel):
    """Definition of template and paths to its file."""
    template_name: str = SettingsField(
        "",
        title="Template name"
    )
    path: MultiplatformPathModel = SettingsField(
        default_factory=MultiplatformPathModel
    )


class TemplateProfileModel(BaseSettingsModel):
    """Profile to choose multiple templates for single task"""
    task_types: list[str] = SettingsField(
        default_factory=list,
        title="Task types",
        enum_resolver=task_types_enum
    )
    task_names: list[str] = SettingsField(
        default_factory=list,
        title="Task names"
    )
    templates: list[TemplatePathModel] = SettingsField(
        default_factory=list
    )


class MultipleTemplatesModel(BaseSettingsModel):
    profiles: list[TemplateProfileModel] = SettingsField(
        default_factory=list
    )

