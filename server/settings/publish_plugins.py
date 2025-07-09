from ayon_server.settings import BaseSettingsModel, SettingsField


create_flatten_image_enum = [
    {"value": "flatten_with_images", "label": "Flatten with images"},
    {"value": "flatten_only", "label": "Flatten only"},
    {"value": "no", "label": "No"},
]


color_code_enum = [
    {"value": "red", "label": "Red"},
    {"value": "orange", "label": "Orange"},
    {"value": "yellowColor", "label": "Yellow"},
    {"value": "grain", "label": "Green"},
    {"value": "blue", "label": "Blue"},
    {"value": "violet", "label": "Violet"},
    {"value": "gray", "label": "Gray"},
]


class ColorCodeMappings(BaseSettingsModel):
    color_code: list[str] = SettingsField(
        title="Color codes for layers",
        default_factory=list,
        enum_resolver=lambda: color_code_enum,
    )

    layer_name_regex: list[str] = SettingsField(
        default_factory=list,
        title="Layer name regex"
    )

    product_type: str = SettingsField(
        "",
        title="Resulting product type"
    )

    product_name_template: str = SettingsField(
        "",
        title="Product name template"
    )


class ExtractedOptions(BaseSettingsModel):
    tags: list[str] = SettingsField(
        title="Tags",
        default_factory=list
    )


class CollectColorCodedInstancesPlugin(BaseSettingsModel):
    """Set color for publishable layers, set its resulting product type
    and template for product name. \n Can create flatten image from published
    instances.
    (Applicable only for remote publishing!)"""

    enabled: bool = SettingsField(True, title="Enabled")
    create_flatten_image: str = SettingsField(
        "",
        title="Create flatten image",
        enum_resolver=lambda: create_flatten_image_enum,
    )

    flatten_product_name_template: str = SettingsField(
        "",
        title="Product name template for flatten image"
    )

    color_code_mapping: list[ColorCodeMappings] = SettingsField(
        title="Color code mappings",
        default_factory=ColorCodeMappings,
    )


class CollectReviewPlugin(BaseSettingsModel):
    """Should review product be created"""
    enabled: bool = SettingsField(True, title="Enabled")


class CollectVersionPlugin(BaseSettingsModel):
    """Synchronize version for image and review instances by workfile version"""  # noqa
    enabled: bool = SettingsField(True, title="Enabled")


class ValidateNamingPlugin(BaseSettingsModel):
    """Validate naming of products and layers"""  # noqa
    invalid_chars: str = SettingsField(
        '',
        title="Regex pattern of invalid characters"
    )

    replace_char: str = SettingsField(
        '',
        title="Replacement character"
    )


class ExtractImagePlugin(BaseSettingsModel):
    """Currently only jpg and png are supported"""
    formats: list[str] = SettingsField(
        title="Extract Formats",
        default_factory=list,
    )


class ExtractSourceReviewPlugin(BaseSettingsModel):
    make_image_sequence: bool = SettingsField(
        False,
        title="Make an image sequence instead of flatten image"
    )


class ExtractLayersPlugin(BaseSettingsModel):
    """Export layers within the instance layerset to a PSD file."""
    enabled: bool = SettingsField(False, title="Enabled")
    merge_layersets: bool = SettingsField(
        False,
        title="Merge Layersets",
        description="Merge all layersets within the instance set.",
    )


class PhotoshopPublishPlugins(BaseSettingsModel):
    CollectColorCodedInstances: CollectColorCodedInstancesPlugin = (
        SettingsField(
            title="Collect Color Coded Instances",
            default_factory=CollectColorCodedInstancesPlugin,
        )
    )
    CollectReview: CollectReviewPlugin = SettingsField(
        title="Collect Review",
        default_factory=CollectReviewPlugin,
    )

    CollectVersion: CollectVersionPlugin = SettingsField(
        title="Collect Version",
        default_factory=CollectVersionPlugin,
    )

    ValidateNaming: ValidateNamingPlugin = SettingsField(
        title="Validate naming of products and layers",
        default_factory=ValidateNamingPlugin,
    )

    ExtractImage: ExtractImagePlugin = SettingsField(
        title="Extract Image",
        default_factory=ExtractImagePlugin,
    )

    ExtractSourcesReview: ExtractSourceReviewPlugin = SettingsField(
        title="Extract Sources for Review",
        default_factory=ExtractSourceReviewPlugin,
    )

    ExtractLayers: ExtractLayersPlugin = SettingsField(
        title="Extract Layers",
        default_factory=ExtractLayersPlugin,
    )


DEFAULT_PUBLISH_SETTINGS = {
    "CollectColorCodedInstances": {
        "create_flatten_image": "no",
        "flatten_product_name_template": "",
        "color_code_mapping": []
    },
    "CollectReview": {
        "enabled": True
    },
    "CollectVersion": {
        "enabled": False
    },
    "ValidateNaming": {
        "invalid_chars": "[ \\\\/+\\*\\?\\(\\)\\[\\]\\{\\}:,;]",
        "replace_char": "_"
    },
    "ExtractImage": {
        "formats": [
            "png",
            "jpg",
            "tga"
        ]
    },
    "ExtractSourcesReview": {
        "make_image_sequence": False,
    },
    "ExtractLayers": {
        "enabled": False,
        "merge_layersets": False
    }
}
