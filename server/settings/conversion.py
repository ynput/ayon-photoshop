from typing import Any


def _convert_color_coded_mapping_0_4_0(overrides):
    color_coded_mapping_overrides = (
        overrides.get("publish", {})
        .get("CollectColorCodedInstances", {})
        .get("color_code_mapping")
    )
    if not color_coded_mapping_overrides:
        return

    for mapping in color_coded_mapping_overrides:
        if "product_base_type" not in mapping and "product_type" in mapping:
            mapping["product_base_type"] = mapping.pop("product_type")


def convert_settings_overrides(
    source_version: str,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    _convert_color_coded_mapping_0_4_0(overrides)
    return overrides
