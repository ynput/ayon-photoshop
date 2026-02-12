"""
Requires:
    None

Provides:
    instance     -> productBaseType ("review")
"""
import pyblish.api

from ayon_photoshop import api as photoshop
from ayon_core.pipeline.create import get_product_name


class CollectAutoReview(pyblish.api.ContextPlugin):
    """Create review instance in non artist based workflow.

    Called only if PS is triggered in Webpublisher or in tests.
    """

    label = "Collect Auto Review"
    hosts = ["photoshop"]
    order = pyblish.api.CollectorOrder + 0.2
    targets = ["automated"]

    publish = True

    def process(self, context):
        has_review = False
        for instance in context:
            if instance.data["productBaseType"] == "review":
                has_review = True

            creator_attributes = instance.data.get("creator_attributes", {})
            if (
                creator_attributes.get("mark_for_review")
                and "review" not in instance.data["families"]
            ):
                instance.data["families"].append("review")

        if has_review:
            self.log.debug("Review instance found, won't create new")
            return

        proj_settings = context.data["project_settings"]
        auto_creator = proj_settings["photoshop"]["create"]["ReviewCreator"]

        if not auto_creator["enabled"]:
            self.log.debug("Review creator disabled, won't create new")
            return

        stub = photoshop.stub()
        stored_items = stub.get_layers_metadata()
        for item in stored_items:
            if item.get("creator_identifier") == "review":
                if not item.get("active"):
                    self.log.debug("Review instance disabled")
                    return

        variant = (
            context.data.get("variant")
            or auto_creator["default_variant"]
        )

        project_name = context.data["projectName"]
        host_name = context.data["hostName"]
        folder_entity = context.data["folderEntity"]
        task_entity = context.data["taskEntity"]

        product_base_type = "review"
        # QUESTION how to define product type for auto collector?
        product_type = product_base_type

        product_name = get_product_name(
            project_name=project_name,
            host_name=host_name,
            product_base_type=product_base_type,
            product_type=product_type,
            variant=variant,
            project_settings=proj_settings,
            folder_entity=folder_entity,
            task_entity=task_entity,
        )

        instance = context.create_instance(product_name)
        instance.data.update({
            "label": product_name,
            "name": product_name,
            "productName": product_name,
            "productType": product_type,
            "productBaseType": product_base_type,
            "family": product_base_type,
            "families": [product_base_type],
            "representations": [],
            "folderPath": folder_entity["path"],
            "publish": self.publish
        })

        self.log.debug("auto review created::{}".format(instance.data))
