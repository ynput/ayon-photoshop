import os

import pyblish.api


class CollectWorkfile(pyblish.api.InstancePlugin):
    """Collect current script for publish."""

    order = pyblish.api.CollectorOrder - 0.4
    label = "Collect Workfile"
    hosts = ["photoshop"]
    families = ["workfile"]
    targets = ["local"]

    default_variant = "Main"

    def process(self, instance):
        file_path = instance.context.data["currentFile"]
        ext = os.path.splitext(file_path)[1].lstrip(".")
        staging_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)

        # creating representation
        instance.data["representations"].append({
            "name": ext,
            "ext": ext,
            "files": base_name,
            "stagingDir": staging_dir,
        })
