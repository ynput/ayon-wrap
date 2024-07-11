from pydantic import Field

from ayon_server.settings import (
    BaseSettingsModel,
    MultiplatformPathModel,
    task_types_enum,
    SettingsField
)


class CustomBuilderTemplate(BaseSettingsModel):
    task_types: list[str] = SettingsField(
        default_factory=list,
        title="Task types",
        enum_resolver=task_types_enum
    )
    task_names: list[str] = SettingsField(
        default_factory=list,
        title="Task names"
    )
    path: MultiplatformPathModel = SettingsField(
        default_factory=MultiplatformPathModel
    )


class WorkfileBuilderPlugin(BaseSettingsModel):
    _title = "Workfile Builder"
    create_first_version: bool = SettingsField(
        False,
        title="Create first workfile"
    )

    custom_templates: list[CustomBuilderTemplate] = SettingsField(
        default_factory=list
    )
