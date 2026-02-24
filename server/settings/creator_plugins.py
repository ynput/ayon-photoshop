from ayon_server.settings import BaseSettingsModel, SettingsField


class ProductTypeItemModel(BaseSettingsModel):
    _layout = "compact"
    product_type: str = SettingsField(
        title="Product type",
        description="Product type name",
    )
    label: str = SettingsField(
        "",
        title="Label",
        description="Label to display in UI for the product type",
    )


class CreateImagePluginModel(BaseSettingsModel):
    enabled: bool = SettingsField(True, title="Enabled")
    active_on_create: bool = SettingsField(True, title="Active by default")
    mark_for_review: bool = SettingsField(False, title="Review by default")
    default_variants: list[str] = SettingsField(
        default_factory=list,
        title="Default Variants"
    )
    product_type_items: list[ProductTypeItemModel] = SettingsField(
        default_factory=list,
        title="Product type items",
        description=(
            "Optional list of product types that this plugin can create."
        )
    )


class AutoImageCreatorPluginModel(BaseSettingsModel):
    enabled: bool = SettingsField(False, title="Enabled")
    active_on_create: bool = SettingsField(True, title="Active by default")
    mark_for_review: bool = SettingsField(False, title="Review by default")
    default_variant: str = SettingsField("", title="Default Variants")


class CreateReviewPlugin(BaseSettingsModel):
    enabled: bool = SettingsField(True, title="Enabled")
    active_on_create: bool = SettingsField(True, title="Active by default")
    default_variant: str = SettingsField("", title="Default Variants")
    product_type_items: list[ProductTypeItemModel] = SettingsField(
        default_factory=list,
        title="Product type items",
        description=(
            "Optional list of product types that this plugin can create."
        )
    )


class CreateWorkfilelugin(BaseSettingsModel):
    enabled: bool = SettingsField(True, title="Enabled")
    active_on_create: bool = SettingsField(True, title="Active by default")
    default_variant: str = SettingsField("", title="Default Variants")


class PhotoshopCreatorPlugins(BaseSettingsModel):
    ImageCreator: CreateImagePluginModel = SettingsField(
        title="Create Image",
        default_factory=CreateImagePluginModel,
    )
    AutoImageCreator: AutoImageCreatorPluginModel = SettingsField(
        title="Create Flatten Image",
        default_factory=AutoImageCreatorPluginModel,
    )
    ReviewCreator: CreateReviewPlugin = SettingsField(
        title="Create Review",
        default_factory=CreateReviewPlugin,
    )
    WorkfileCreator: CreateWorkfilelugin = SettingsField(
        title="Create Workfile",
        default_factory=CreateWorkfilelugin,
    )


DEFAULT_CREATE_SETTINGS = {
    "ImageCreator": {
        "enabled": True,
        "active_on_create": True,
        "mark_for_review": False,
        "default_variants": [
            "Main"
        ]
    },
    "AutoImageCreator": {
        "enabled": False,
        "active_on_create": True,
        "mark_for_review": False,
        "default_variant": ""
    },
    "ReviewCreator": {
        "enabled": True,
        "active_on_create": True,
        "default_variant": ""
    },
    "WorkfileCreator": {
        "enabled": True,
        "active_on_create": True,
        "default_variant": "Main"
    }
}
