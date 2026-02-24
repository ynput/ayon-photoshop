import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishXmlValidationError,
    OptionalPyblishPluginMixin,
)
from ayon_photoshop import api as photoshop


def _normalize_mode(mode_value):
    if not mode_value:
        return ""
    return mode_value.split(".")[-1].upper()


def _normalize_bits(bits_value):
    if not bits_value:
        return None
    value = bits_value.upper()
    if "SIXTEEN" in value:
        return 16
    if "EIGHT" in value:
        return 8
    if "THIRTYTWO" in value or "THIRTY_TWO" in value:
        return 32
    try:
        return int(float(bits_value))
    except (ValueError, TypeError):
        return None


class ValidateDocumentSettingsRepair(pyblish.api.Action):
    """Repair document settings to match expected values.

    Warning: Some conversions may be lossy (e.g., CMYK to RGB,
    higher to lower bit depth).
    """

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):
        stub = photoshop.stub()

        result = stub.set_document_settings(
            resolution=plugin.expected_dpi,
            mode=plugin.expected_mode,
            bits=str(plugin.expected_bits)
        )

        if not result.get("success"):
            errors = result.get("errors") or [result.get("error", "Unknown")]
            self.log.error(
                "Failed to repair document settings: {}".format(
                    ", ".join(errors)
                )
            )
            return False

        self.log.info("Document settings repaired successfully")
        return True


class ValidateDocumentSettings(
    pyblish.api.ContextPlugin, OptionalPyblishPluginMixin
):
    """Validate document resolution, color mode and bit depth."""

    label = "Validate Document Settings"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"
    actions = [ValidateDocumentSettingsRepair]

    optional = True
    active = True

    expected_dpi = 72
    expected_mode = "RGB"
    expected_bits = 16

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_settings()
        if not info:
            raise PublishXmlValidationError(
                self,
                "Unable to read document settings from Photoshop.",
                formatting_data={
                    "details": "Unable to read document settings.",
                    "expected_dpi": self.expected_dpi,
                    "expected_mode": self.expected_mode,
                    "expected_bits": self.expected_bits,
                },
            )

        invalid: bool = False

        resolution = info.get("resolution")
        try:
            resolution_value = int(round(float(resolution)))
        except (ValueError, TypeError):
            resolution_value = None
        if resolution_value != int(self.expected_dpi):
            self.log.warning(
                f"Resolution is {resolution_value} dpi"
                f" (expected {self.expected_dpi} dpi)"
            )
            invalid = True

        mode = _normalize_mode(info.get("mode"))
        if mode != self.expected_mode.upper():
            mode_label = mode or info.get("mode")
            self.log.warning(
                f"Color mode is {mode_label} (expected {self.expected_mode})"
            )
            invalid = True

        bits = _normalize_bits(info.get("bitsPerChannel"))
        if bits != int(self.expected_bits):
            self.log.warning(
                f"Bit depth is {bits} (expected {self.expected_bits})"
            )
            invalid = True

        if invalid:
            raise PublishXmlValidationError(
                self,
                "Document settings are not compliant.",
                formatting_data={
                    "expected_dpi": self.expected_dpi,
                    "expected_mode": self.expected_mode,
                    "expected_bits": self.expected_bits,
                }
            )
