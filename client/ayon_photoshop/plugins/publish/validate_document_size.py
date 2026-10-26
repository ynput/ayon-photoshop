import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    OptionalPyblishPluginMixin,
    PublishXmlValidationError
)
from ayon_photoshop import api as photoshop
from ayon_photoshop.api.lib import PSD_MAX_DIMENSION, document_requires_psb


class ValidateDocumentSize(
    pyblish.api.ContextPlugin,
    OptionalPyblishPluginMixin
):
    """Validate the document is within the safe size limits for publishing.

    Very large documents cannot be handled by every representation type:
    review/preview encoding (ffmpeg) fails above roughly 268 Mpx and huge
    PSD/PSB/PNG exports produce multi-GB files that are slow to write and
    transfer. The workfile and layer extractions are converted to PSB by the
    publishers themselves, this validator only informs the artist about the
    remaining limitations before any extraction starts.

    The validation is optional, so it can be disabled as a workaround when
    the document has to be published anyway.
    """

    label = "Validate Document Size"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"

    optional = True
    active = True

    # Configured by settings. Documents above this pixel count can fail
    # review/thumbnail extraction (ffmpeg) and produce multi-GB staging files.
    max_pixels = 100_000_000

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_size() or {}
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        pixels = width * height
        max_pixels = int(self.max_pixels or 0)

        exceeds_psd_limit = document_requires_psb(info)
        exceeds_max_pixels = bool(max_pixels and pixels > max_pixels)
        if not exceeds_psd_limit and not exceeds_max_pixels:
            return

        reasons = []
        if exceeds_psd_limit:
            reasons.append(
                f"a side is at or above the {PSD_MAX_DIMENSION} px PSD limit"
            )
        if exceeds_max_pixels:
            reasons.append(
                f"it has {pixels:,} px, above the configured limit of "
                f"{max_pixels:,} px"
            )
        msg = (
            f"Document is {width}x{height} px ({pixels:,} px): "
            + "; ".join(reasons) + "."
        )
        formatting_data = {
            "msg": msg,
            "width": width,
            "height": height,
            "pixels": f"{pixels:,}",
            "max_dimension": PSD_MAX_DIMENSION,
            "max_pixels": f"{max_pixels:,}" if max_pixels else "not limited",
        }
        raise PublishXmlValidationError(
            self, msg, formatting_data=formatting_data
        )
