from pydantic import Field
from ayon_server.settings import BaseSettingsModel
from .templated_workfile_build import TemplatedWorkfileBuildModel


class WrapSettings(BaseSettingsModel):
    """Wrap Project Settings."""

    templated_workfile_build: TemplatedWorkfileBuildModel = Field(
        default_factory=TemplatedWorkfileBuildModel,
        title="Templated Workfile Build Settings"
    )


DEFAULT_WRAP_SETTING = {

}
