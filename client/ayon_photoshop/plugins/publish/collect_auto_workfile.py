import os
import pyblish.api

from ayon_photoshop import api as photoshop
from ayon_core.pipeline.create import get_product_name


class CollectAutoWorkfile(pyblish.api.ContextPlugin):
    """Collect current script for publish."""

    order = pyblish.api.CollectorOrder + 0.2
    label = "Collect Workfile"
    hosts = ["photoshop"]

    targets = ["automated"]

    def process(self, context):
        file_path = context.data["currentFile"]
        _, ext = os.path.splitext(file_path)
        staging_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        workfile_representation = {
            "name": ext[1:],
            "ext": ext[1:],
            "files": base_name,
            "stagingDir": staging_dir,
        }
        workfile_instance = self._find_workfile_instance(context)
        if workfile_instance:
            self.log.debug("Workfile instance found, won't create new")
            workfile_instance.data.update({
                "label": base_name,
                "name": base_name,
                "representations": [workfile_representation],
            })
            return

        stub = photoshop.stub()
        stored_items = stub.get_layers_metadata()
        for item in stored_items:
            if item.get("creator_identifier") == "workfile":
                if not item.get("active"):
                    self.log.debug("Workfile instance disabled")
                    return

        project_name = context.data["projectName"]
        proj_settings = context.data["project_settings"]
        auto_creator = proj_settings["photoshop"]["create"]["WorkfileCreator"]

        if not auto_creator["enabled"]:
            self.log.debug("Workfile creator disabled, won't create new")
            return

        product_base_type = "workfile"
        # context.data["variant"] might come only from collect_batch_data
        variant = (
            context.data.get("variant")
            or auto_creator["default_variant"]
        )

        host_name = context.data["hostName"]
        folder_entity = context.data["folderEntity"]
        task_entity = context.data["taskEntity"]

        product_name = get_product_name(
            project_name=project_name,
            folder_entity=folder_entity,
            task_entity=task_entity,
            host_name=host_name,
            product_base_type=product_base_type,
            product_type=product_base_type,
            variant=variant,
            project_settings=proj_settings,
        )

        # Create instance
        instance = context.create_instance(product_name)
        instance.data.update({
            "label": base_name,
            "name": base_name,
            "productName": product_name,
            "productType": product_base_type,
            "productBaseType": product_base_type,
            "family": product_base_type,
            "families": [product_base_type],
            "representations": [workfile_representation],
            "folderPath": folder_entity["path"]
        })

        self.log.debug(f"auto workfile review created:{instance.data}")

    def _find_workfile_instance(self, context):
        for instance in context:
            product_base_type = instance.data.get("productBaseType")
            if not product_base_type:
                product_base_type = instance.data["productType"]

            if product_base_type == "workfile":
                return instance
        return None
