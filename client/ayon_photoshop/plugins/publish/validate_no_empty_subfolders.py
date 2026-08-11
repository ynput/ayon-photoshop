import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishXmlValidationError,
    OptionalPyblishPluginMixin,
)
from ayon_photoshop import api as photoshop


class ValidateEmptyImagemainFoldersRepair(pyblish.api.Action):
    """Delete empty sub-folders (groups) found inside 'imagemain'."""

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):
        stub = photoshop.stub()
        empty_groups = plugin.get_empty_groups(stub)

        if not empty_groups:
            self.log.info("No empty sub-folder to remove.")
            return True

        for group in empty_groups:
            self.log.info(f"Deleting empty group '{group.clean_name}'")
            stub.delete_layer(group.id)

        return True


class ValidateEmptyImagemainFolders(
    pyblish.api.ContextPlugin, OptionalPyblishPluginMixin
):
    """Validate there are no empty sub-folders inside 'imageMain' at every level."""

    label = "Validate Empty Imagemain Folders"
    hosts = ["photoshop"]
    order = ValidateContentsOrder
    settings_category = "photoshop"
    actions = [ValidateEmptyImagemainFoldersRepair]

    optional = True
    active = True

    root_group_name: str = "imageMain"

    @classmethod
    def get_empty_groups(cls, stub):
        layers = stub.get_layers()
        children_layer = {None: []}
        for layer in layers:
            parent_id = layer.parents[-1] if layer.parents else None
            children_layer.setdefault(parent_id, []).append(layer)

        root = next(
            (
                layer
                for layer in layers
                if layer.group
                and layer.clean_name.lower() == cls.root_group_name.lower()
            ),
            None,
        )
        if root is None:
            return []

        empty_groups = []
        to_visit = [
            child for child in children_layer.get(root.id, [])
            if child.group
        ]

        while to_visit:
            group = to_visit.pop()
            children = children_layer.get(group.id, [])
            if not children:
                empty_groups.append(group)
            else:
                to_visit.extend(c for c in children if c.group)

        return empty_groups

    def process(self, context):
        if not self.is_active(context.data):
            return

        stub = photoshop.stub()
        empty_groups = self.get_empty_groups(stub)

        if not empty_groups:
            return

        names = ", ".join(group.clean_name for group in empty_groups)
        raise PublishXmlValidationError(
            self,
            f"Empty sub-folder(s) found inside '{self.root_group_name}': "
            f"{names}. Empty groups block the layer merge used to "
            "produce the render and must be removed before publishing.",
            formatting_data={
                "empty_folders": names,
                "root_group_name": self.root_group_name,
            },
        )