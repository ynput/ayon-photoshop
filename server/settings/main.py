from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import PhotoshopImageIOModel
from .creator_plugins import PhotoshopCreatorPlugins, DEFAULT_CREATE_SETTINGS
from .publish_plugins import PhotoshopPublishPlugins, DEFAULT_PUBLISH_SETTINGS
from .workfile_builder import WorkfileBuilderPlugin


default_workfile_extensions_enum = [
    {"value": ".psd", "label": "psd"},
    {"value": ".psb", "label": "psb"},
]


class PhotoshopSettings(BaseSettingsModel):
    """Photoshop Project Settings."""

    auto_install_extension: bool = SettingsField(
        False,
        title="Install AYON Extension",
        description="Triggers pre-launch hook which installs extension."
    )
    default_workfile_extension: str = SettingsField(
        ".psd",
        title="Default workfile extension",
        description="Default extension used when saving workfiles.",
        enum_resolver=lambda: default_workfile_extensions_enum,
    )

    imageio: PhotoshopImageIOModel = SettingsField(
        default_factory=PhotoshopImageIOModel,
        title="OCIO config"
    )

    create: PhotoshopCreatorPlugins = SettingsField(
        default_factory=PhotoshopCreatorPlugins,
        title="Creator plugins"
    )

    publish: PhotoshopPublishPlugins = SettingsField(
        default_factory=PhotoshopPublishPlugins,
        title="Publish plugins"
    )

    workfile_builder: WorkfileBuilderPlugin = SettingsField(
        default_factory=WorkfileBuilderPlugin,
        title="Workfile Builder"
    )


DEFAULT_PHOTOSHOP_SETTING = {
    "auto_install_extension": True,
    "default_workfile_extension": ".psd",
    "create": DEFAULT_CREATE_SETTINGS,
    "publish": DEFAULT_PUBLISH_SETTINGS,
    "workfile_builder": {
        "create_first_version": False,
        "custom_templates": []
    }
}
