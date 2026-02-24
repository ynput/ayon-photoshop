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

color_mode_enum = [
    {"value": "RGB", "label": "RGB"},
    {"value": "CMYK", "label": "CMYK"},
    {"value": "GRAYSCALE", "label": "Grayscale"},
    {"value": "LAB", "label": "Lab"},
    {"value": "BITMAP", "label": "Bitmap"},
    {"value": "DUOTONE", "label": "Duotone"},
    {"value": "INDEXEDCOLOR", "label": "Indexed Color"},
    {"value": "MULTICHANNEL", "label": "Multichannel"},
]

bit_depth_enum = [
    {"value": "8", "label": "8 bits"},
    {"value": "16", "label": "16 bits"},
    {"value": "32", "label": "32 bits"},
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

    product_base_type: str = SettingsField(
        "",
        title="Resulting product base type"
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
    """Set color for publishable layers, set its resulting product base type
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


class ValidateDocumentSettingsPlugin(BaseSettingsModel):
    """Validate document resolution, color mode and bit depth."""
    enabled: bool = SettingsField(True, title="Enabled")
    optional: bool = SettingsField(True, title="Optional")
    active: bool = SettingsField(True, title="Active")
    expected_dpi: int = SettingsField(72, title="Expected DPI")
    expected_mode: str = SettingsField(
        "RGB",
        title="Expected Color Mode",
        enum_resolver=lambda: color_mode_enum,
    )
    expected_bits: str = SettingsField(
        "8",
        title="Expected Bit Depth",
        enum_resolver=lambda: bit_depth_enum,
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

    ValidateDocumentSettings: ValidateDocumentSettingsPlugin = SettingsField(
        title="Validate Document Settings",
        default_factory=ValidateDocumentSettingsPlugin,
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
    "ExtractSourcesReview": {
        "make_image_sequence": False,
    },
    "ExtractLayers": {
        "enabled": False,
        "merge_layersets": False
    },
    "ValidateDocumentSettings": {
        "enabled": False,
        "optional": True,
        "active": True,
        "expected_dpi": 72,
        "expected_mode": "RGB",
        "expected_bits": "8"
    }
}
