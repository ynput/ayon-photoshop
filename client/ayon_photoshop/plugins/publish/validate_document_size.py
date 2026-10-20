import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    OptionalPyblishPluginMixin,
)
from ayon_photoshop import api as photoshop


class ValidateDocumentSize(
    pyblish.api.ContextPlugin,
    OptionalPyblishPluginMixin
):
    """Warn when the document is too large for some representations.

    Very large documents cannot be handled by every representation type:
    review/preview encoding (ffmpeg) fails above roughly 268 Mpx and huge
    PSD/PSB/PNG exports produce multi-GB files that are slow to write and
    transfer. The workfile and layer extractions are converted to PSB by the
    publishers themselves, this validator only informs the artist about the
    remaining limitations before any extraction starts.
    """

    label = "Validate Document Size"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"

    optional = True
    active = True

    # Above this pixel count review/thumbnail extraction and large format
    # exports can fail or produce very large staging files.
    max_pixels = 100_000_000

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_size() or {}
        width = info.get("width") or 0
        height = info.get("height") or 0
        if not width or not height:
            return

        pixels = width * height
        if pixels > self.max_pixels:
            self.log.warning(
                "Document is %dx%d (%s px), above the %s px safe limit. "
                "Review/preview extraction and very large representations "
                "may fail or produce multi-GB staging files; consider "
                "downscaling the document or disabling those "
                "representations.",
                width,
                height,
                f"{pixels:,}",
                f"{self.max_pixels:,}",
            )
