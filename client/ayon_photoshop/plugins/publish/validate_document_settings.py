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


class ValidateDocumentSettings(
    pyblish.api.ContextPlugin, OptionalPyblishPluginMixin
):
    """Validate document resolution, color mode and bit depth."""

    label = "Validate Document Settings"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"

    optional = True
    active = True

    expected_dpi = 72
    expected_mode = "RGB"
    expected_bits = 16

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_info()
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

        issues = []

        resolution = info.get("resolution")
        try:
            resolution_value = int(round(float(resolution)))
        except (ValueError, TypeError):
            resolution_value = None
        if resolution_value != int(self.expected_dpi):
            issues.append(
                "Resolution is {} dpi (expected {} dpi)".format(
                    resolution_value, self.expected_dpi
                )
            )

        mode = _normalize_mode(info.get("mode"))
        if mode != self.expected_mode.upper():
            issues.append(
                "Color mode is {} (expected {})".format(
                    mode or info.get("mode"), self.expected_mode
                )
            )

        bits = _normalize_bits(info.get("bitsPerChannel"))
        if bits != int(self.expected_bits):
            issues.append(
                "Bit depth is {} (expected {})".format(
                    bits, self.expected_bits
                )
            )

        if issues:
            raise PublishXmlValidationError(
                self,
                "Document settings are not compliant.",
                formatting_data={
                    "details": "\n".join(issues),
                    "expected_dpi": self.expected_dpi,
                    "expected_mode": self.expected_mode,
                    "expected_bits": self.expected_bits,
                }
            )
