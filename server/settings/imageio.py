from pydantic import validator
from ayon_server.settings import BaseSettingsModel, SettingsField
from ayon_server.settings.validators import ensure_unique_names


class ImageIOFileRuleModel(BaseSettingsModel):
    name: str = SettingsField("", title="Rule name")
    pattern: str = SettingsField("", title="Regex pattern")
    colorspace: str = SettingsField("", title="Colorspace name")
    ext: str = SettingsField("", title="File extension")


class ImageIOFileRulesModel(BaseSettingsModel):
    activate_host_rules: bool = SettingsField(False)
    rules: list[ImageIOFileRuleModel] = SettingsField(
        default_factory=list,
        title="Rules"
    )

    @validator("rules")
    def validate_unique_outputs(cls, value):
        ensure_unique_names(value)
        return value


class ImageIORemappingRulesModel(BaseSettingsModel):
    host_native_name: str = SettingsField(
        title="Application native colorspace name"
    )
    ocio_name: str = SettingsField(title="OCIO colorspace name")


class ImageIORemappingModel(BaseSettingsModel):
    rules: list[ImageIORemappingRulesModel] = SettingsField(
        default_factory=list)


class PhotoshopImageIOModel(BaseSettingsModel):
    activate_host_color_management: bool = SettingsField(
        True, title="Enable Color Management"
    )
    remapping: ImageIORemappingModel = SettingsField(
        title="Remapping colorspace names",
        default_factory=ImageIORemappingModel
    )
    file_rules: ImageIOFileRulesModel = SettingsField(
        default_factory=ImageIOFileRulesModel,
        title="File Rules"
    )
