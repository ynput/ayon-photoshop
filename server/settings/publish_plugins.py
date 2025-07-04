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

extract_image_ext_enum = [
    {"value": "png", "label": "png"},
    {"value": "jpg", "label": "jpg"},
    {"value": "tga", "label": "tga"},
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
    """Extracts image products and representations per published instance"""

    formats: list[str] = SettingsField(
        title="Extract Formats",
        default_factory=list,
        enum_resolver=lambda: extract_image_ext_enum,
    )


class ExtractReviewPlugin(BaseSettingsModel):
    make_image_sequence: bool = SettingsField(
        False,
        title="Make an image sequence instead of flatten image"
    )

    max_downscale_size: int = SettingsField(
        8192,
        title="Maximum size of sources for review",
        description="FFMpeg can only handle limited resolution for creation of review and/or thumbnail",  # noqa
        gt=300,  # greater than
        le=16384,  # less or equal
    )

    jpg_options: ExtractedOptions = SettingsField(
        title="Extracted jpg Options",
        default_factory=ExtractedOptions
    )

    mov_options: ExtractedOptions = SettingsField(
        title="Extracted mov Options",
        default_factory=ExtractedOptions
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

    ExtractReview: ExtractReviewPlugin = SettingsField(
        title="Extract Review",
        default_factory=ExtractReviewPlugin,
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
        ]
    },
    "ExtractReview": {
        "make_image_sequence": False,
        "max_downscale_size": 8192,
        "jpg_options": {
            "tags": [
                "review",
                "ftrackreview",
                "webreview"
            ]
        },
        "mov_options": {
            "tags": [
                "review",
                "ftrackreview",
                "webreview"
            ]
        }
    },
    "ExtractLayers": {
        "enabled": False,
        "merge_layersets": False
    }
}
