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


class WorkfileTemplateModel(BaseSettingsModel):
    directory_template: str = SettingsField(
        "",
        title="Directory template"
    )
    filename_template: str = SettingsField(
        "",
        title="File name template"
    )


class MultipleTemplatesModel(BaseSettingsModel):
    workfile_template: WorkfileTemplateModel = SettingsField(
        default_factory=WorkfileTemplateModel,
        title="Workfile template", 
        description="Configure enhanced workfile path template by template name"
    )
    profiles: list[TemplateProfileModel] = SettingsField(
        default_factory=list
    )

