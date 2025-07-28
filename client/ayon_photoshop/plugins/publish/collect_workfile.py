import os

import pyblish.api


class CollectWorkfile(pyblish.api.InstancePlugin):
    """Collect current script for publish."""

    order = pyblish.api.CollectorOrder + 0.1
    label = "Collect Workfile"
    hosts = ["photoshop"]
    families = ["workfile"]

    default_variant = "Main"

    def process(self, instance):
        file_path = instance.context.data["currentFile"]
        _, ext = os.path.splitext(file_path)
        staging_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)

        # creating representation
        _, ext = os.path.splitext(file_path)
        instance.data["representations"].append({
            "name": ext[1:],
            "ext": ext[1:],
            "files": base_name,
            "stagingDir": staging_dir,
        })
