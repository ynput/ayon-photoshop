import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishXmlValidationError,
    OptionalPyblishPluginMixin,
)
from ayon_photoshop import api as photoshop


class ValidateSmartObjectLinksRepair(pyblish.api.Action):
    """Rasterise broken Smart Object layers and re-embed them as local objects.

    Warning: This repair is destructive — the original linked content is
    replaced by a rasterised snapshot that is re-wrapped as an embedded Smart
    Object.  Consider relinking the original sources manually if you want to
    preserve editability.
    """

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):
        stub = photoshop.stub()
        fixed = stub.fix_broken_smart_object_links()
        if fixed:
            self.log.info(
                "Repaired {} layer(s): {}".format(len(fixed), ", ".join(fixed))
            )
        else:
            self.log.warning(
                "Repair ran but no layers were modified. "
                "Please check the document manually."
            )


class ValidateSmartObjectLinks(
    pyblish.api.ContextPlugin, OptionalPyblishPluginMixin
):
    """Validate that no Smart Object layers have broken or missing links.

    Checks both locally linked files (link.status == missing / unresolved)
    and CC Libraries assets (linkMissing flag).  Broken links prevent correct
    rendering and must be resolved before publishing.
    """

    label = "Validate Smart Object Links"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"
    actions = [ValidateSmartObjectLinksRepair]

    optional = True
    active = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        stub = photoshop.stub()
        broken = stub.get_broken_smart_object_links()

        if broken:
            names = ", ".join(broken)
            raise PublishXmlValidationError(
                self,
                "Broken Smart Object links detected.",
                formatting_data={"broken_layers": names},
            )
