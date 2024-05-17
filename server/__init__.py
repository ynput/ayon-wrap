from ayon_server.addons import BaseServerAddon

from .settings import WrapSettings, DEFAULT_WRAP_SETTING


class WrpAddon(BaseServerAddon):
    settings_model = WrapSettings


    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_WRAP_SETTING)
