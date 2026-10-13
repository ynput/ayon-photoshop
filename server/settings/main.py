from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import PhotoshopImageIOModel
from .creator_plugins import PhotoshopCreatorPlugins, DEFAULT_CREATE_SETTINGS
from .publish_plugins import PhotoshopPublishPlugins, DEFAULT_PUBLISH_SETTINGS
from .workfile_builder import WorkfileBuilderPlugin


default_workfile_extensions_enum = [
    {"value": ".psd", "label": "psd"},
    {"value": ".psb", "label": "psb"},
]

panel_type_enum = [
    {"value": "cep", "label": "CEP extension"},
    {"value": "uxp", "label": "UXP plugin"},
]


class PhotoshopSettings(BaseSettingsModel):
    """Photoshop Project Settings."""

    panel_type: str = SettingsField(
        "cep",
        title="Panel type",
        description=(
            "Which AYON panel Photoshop uses, only one can be active. "
            "CEP is the legacy extension. UXP is the new plugin, it needs "
            "Photoshop 24+ and the Creative Cloud desktop app to be "
            "installed automatically. The other panel is removed from "
            "Photoshop at launch when 'Install panel automatically' is on."
        ),
        enum_resolver=lambda: panel_type_enum,
    )
    auto_install_extension: bool = SettingsField(
        False,
        title="Install panel automatically",
        description=(
            "Triggers pre-launch hook which installs the panel selected "
            "above and removes the other one."
        ),
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
    "panel_type": "cep",
    "auto_install_extension": True,
    "default_workfile_extension": ".psd",
    "create": DEFAULT_CREATE_SETTINGS,
    "publish": DEFAULT_PUBLISH_SETTINGS,
    "workfile_builder": {
        "create_first_version": False,
        "custom_templates": []
    }
}
