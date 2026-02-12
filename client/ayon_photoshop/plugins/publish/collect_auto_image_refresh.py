import pyblish.api

from ayon_photoshop import api as photoshop


class CollectAutoImageRefresh(pyblish.api.ContextPlugin):
    """Refreshes auto_image instance with currently visible layers..
    """

    label = "Collect Auto Image Refresh"
    hosts = ["photoshop"]
    order = pyblish.api.CollectorOrder + 0.2

    def process(self, context):
        for instance in context:
            creator_identifier = instance.data.get("creator_identifier")
            if creator_identifier == "auto_image":
                # refresh existing auto image instance with current visible
                self.log.debug(
                    "Auto image instance found, filling layer ids to export."
                )
                publishable_ids = [
                    layer.id
                    for layer in photoshop.stub().get_layers()
                    if layer.visible
                ]
                instance.data["ids"] = publishable_ids
                return
