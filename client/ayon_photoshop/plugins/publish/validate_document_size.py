import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    OptionalPyblishPluginMixin,
    PublishXmlValidationError
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
    """Validate that the document can be published as PSD.

    PSD stores up to 30000 x 30000 px and up to 2 GB; above the dimension
    limit Photoshop has to save as PSB. This validator blocks such documents
    with an artist message and is optional, so a studio that deliberately
    works in PSB can disable it.

    The 2 GB file size limit can not be validated up front (it depends on the
    compressed result), those failures are reported by the extractor that
    actually hits them.
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
            # PSD stores up to 30000 px per side and 2 GB; above the dimension
            # limit the document can only be PSB. Blocking here is the point
            # of the validator - it is optional, so a studio that works in PSB
            # can disable it instead of being unable to publish.
            raise PublishXmlValidationError(
                self,
                "Document is {}x{} px, above the {} px PSD dimension limit."
                .format(
                    info.get("width"),
                    info.get("height"),
                    PSD_MAX_DIMENSION,
                ),
                formatting_data={
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "limit": PSD_MAX_DIMENSION,
                },
            )
