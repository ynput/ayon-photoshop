"""
Requires:
    None

Provides:
    instance     -> productType ("review")
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

    # TODO lower order when 'CollectContextEntities' lowers order
    # order = pyblish.api.CollectorOrder - 0.4
    order = pyblish.api.CollectorOrder - 0.09
    targets = ["automated"]

    publish = True

    def process(self, context):
        product_type = "review"
        has_review = False
        for instance in context:
            if instance.data["productType"] == product_type:
                has_review = True
                break

        if has_review:
            self.log.debug("Review instance found, won't create new")
            return

        proj_settings = context.data["project_settings"]
        auto_creator = proj_settings["photoshop"]["create"]["ReviewCreator"]
        if not auto_creator or not auto_creator["enabled"]:
            self.log.debug("Review creator disabled, won't create new")
            return

        stub = photoshop.stub()
        stored_items = stub.get_layers_metadata()
        for item in stored_items:
            if item.get("creator_identifier") == product_type:
                if not item.get("active"):
                    self.log.debug("Review instance disabled")
                    return

        variant = (context.data.get("variant") or
                   auto_creator["default_variant"])

        project_name = context.data["projectName"]
        proj_settings = context.data["project_settings"]
        host_name = context.data["hostName"]
        folder_entity = context.data["folderEntity"]
        task_entity = context.data["taskEntity"]
        task_name = task_type = None
        if task_entity:
            task_name = task_entity["name"]
            task_type = task_entity["taskType"]

        get_product_name_kwargs = {}
        if getattr(get_product_name, "use_entities", False):
            get_product_name_kwargs.update({
                "folder_entity": folder_entity,
                "task_entity": task_entity,
                # TODO (antirotor): handle product_base_type properly
                "product_base_type": product_type,
            })
        else:
            get_product_name_kwargs.update({
                "task_name": task_name,
                "task_type": task_type,
            })

        product_name = get_product_name(
            project_name=project_name,
            host_name=host_name,
            product_type=product_type,
            variant=variant,
            project_settings=proj_settings,
            **get_product_name_kwargs
        )

        instance = context.create_instance(product_name)
        instance.data.update({
            "label": product_name,
            "name": product_name,
            "productName": product_name,
            "productType": product_type,
            # TODO (antirotor): handle product_base_type properly
            "productBaseType": product_type,
            "family": product_type,
            "families": [product_type],
            "representations": [],
            "folderPath": folder_entity["path"],
            "publish": self.publish
        })

        self.log.debug("auto review created::{}".format(instance.data))
