import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    OptionalPyblishPluginMixin,
)
from ayon_photoshop import api as photoshop
from ayon_photoshop.api.lib import (
    document_requires_psb,
    PSD_MAX_DIMENSION
)

class ValidateDocumentSize(
    pyblish.api.ContextPlugin,
    OptionalPyblishPluginMixin
):
    """Warn when the document is too large for PSD.

    PSD stores up to 30000 x 30000 px and up to 2 GB; above that Photoshop
    saves as PSB. That conversion is handled by the host itself (workfile,
    PSD layer extractions), so this plugin only warns. The remaining limits
    (ffmpeg above ~268 Mpx, 2 GB of the raster formats) are reported by the
    extractors when they actually fail, they can not be validated reliably
    up front.
    """

    label = "Validate Document Size"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"

    optional = True
    active = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_size() or {}
        if document_requires_psb(info):
            # A document above the PSD dimension limit is not unpublishable:
            # the workfile and PSD layer extractions are written as PSB by the
            # host itself. Only warn, the extraction failures (2 GB limits of
            # the raster formats) are reported where they actually happen.
            self.log.warning(
                "Document is %sx%s px, above the %s px PSD limit. PSB is "
                "used for workfile/PSD extractions; raster representations "
                "may fail when they exceed 2 GB.",
                info.get("width"),
                info.get("height"),
                PSD_MAX_DIMENSION,
            )
