from ayon_server.addons import BaseServerAddon

from .settings import WrapSettings, DEFAULT_WRAP_SETTING
from .version import __version__


class WrpAddon(BaseServerAddon):
    name = "wrap"
    title = "Wrap"
    version = __version__
    settings_model = WrapSettings


    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_WRAP_SETTING)
