import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    OptionalPyblishPluginMixin,
    PublishXmlValidationError
)
from ayon_photoshop import api as photoshop
from ayon_photoshop.api.lib import document_requires_psb


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

    def process(self, context):
        if not self.is_active(context.data):
            return

        info = photoshop.stub().get_document_size() or {}
        if document_requires_psb(info):
            msg = (
                "Document excceeds 30000 pixels in either width or height."
                "Please reformat the document to fit within the size limits."
            )
            formatting_data = {"msg": msg}
            raise PublishXmlValidationError(
                self, msg, formatting_data=formatting_data
            )
