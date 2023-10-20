from pydantic import Field
from ayon_server.settings import BaseSettingsModel
from .workfile_builder import WorkfileBuilderPlugin


class WrapSettings(BaseSettingsModel):
    """Wrap Project Settings."""

    workfile_builder: WorkfileBuilderPlugin = Field(
        default_factory=WorkfileBuilderPlugin,
        title="Workfile Builder"
    )


DEFAULT_WRAP_SETTING = {

}
