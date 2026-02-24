import pyblish.api

from ayon_core.pipeline import registered_host


class CollectCurrentFile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.49
    label = "Current File"
    hosts = ["photoshop"]

    def process(self, context):
        host = registered_host()
        filename: str = host.get_current_workfile() or ""
        if not filename:
            self.log.debug("Current file appears to be unsaved.")

        self.log.debug(f"Collected current file: '{filename}'")
        context.data["currentFile"] = filename