from ayon_core.pipeline import publish, registered_host


class ExtractSaveScene(publish.Extractor):
    """Save scene before extraction."""

    order = publish.Extractor.order - 0.49
    label = "Extract Save Scene"
    hosts = ["photoshop"]
    families = ["workfile"]

    def process(self, instance):
        host = registered_host()
        path = host.get_current_workfile()
        host.save_workfile(path)
