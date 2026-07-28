from typing import Any

from ayon_server.addons import BaseServerAddon

from .settings import (
    convert_settings_overrides,
    DEFAULT_PHOTOSHOP_SETTING,
    PhotoshopSettings,
)


class Photoshop(BaseServerAddon):
    settings_model = PhotoshopSettings

    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_PHOTOSHOP_SETTING)

    async def convert_settings_overrides(
        self,
        source_version: str,
        overrides: dict[str, Any],
    ) -> dict[str, Any]:
        convert_settings_overrides(source_version, overrides)
        return await super().convert_settings_overrides(
            source_version, overrides
        )
