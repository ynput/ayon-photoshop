import re

from ayon_core.pipeline import get_representation_path
from ayon_photoshop import api as photoshop
from ayon_photoshop.api import get_unique_layer_name


class ImageLoader(photoshop.PhotoshopLoader):
    """Load images

    Stores the imported asset in a container named after the asset.
    """

    product_types = {"image", "render"}
    representations = {"*"}

    def load(self, context, name=None, namespace=None, data=None):
        stub = self.get_stub()
        layer_name = get_unique_layer_name(
            stub.get_layers(),
            context["folder"]["name"],
            name
        )
        with photoshop.maintained_selection():
            path = self.filepath_from_context(context)
            layer = self.import_layer(path, layer_name, stub)

        self[:] = [layer]
        namespace = namespace or layer_name

        return photoshop.containerise(
            name,
            namespace,
            layer,
            context,
            self.__class__.__name__
        )

    def update(self, container, context):
        """ Switch asset or change version """
        stub = self.get_stub()

        layer = container.pop("layer")

        repre_entity = context["representation"]
        folder_name = context["folder"]["name"]
        product_name = context["product"]["name"]

        namespace_from_container = re.sub(r'_\d{3}$', '',
                                          container["namespace"])
        layer_name = "{}_{}".format(folder_name, product_name)
        # switching assets
        if namespace_from_container != layer_name:
            layer_name = get_unique_layer_name(
                stub.get_layers(), folder_name, product_name
            )
        else:  # switching version - keep same name
            layer_name = container["namespace"]

        path = get_representation_path(repre_entity)
        with photoshop.maintained_selection():
            stub.replace_smart_object(
                layer, path, layer_name
            )

        stub.imprint(
            layer.id, {"representation": repre_entity["id"]}
        )

    def remove(self, container):
        """
            Removes element from scene: deletes layer + removes from Headline
        Args:
            container (dict): container to be removed - used to get layer_id
        """
        stub = self.get_stub()

        layer = container.pop("layer")
        stub.imprint(layer.id, {})
        stub.delete_layer(layer.id)

    def switch(self, container, context):
        self.update(container, context)

    def import_layer(self, file_name, layer_name, stub):
        return stub.import_smart_object(file_name, layer_name)

    def _get_colorspace(self, representation: dict) -> Optional[str]:
        """Return Resolve native colorspace from OCIO colorspace data.

        Returns:
            Optional[str]: The Resolve native colorspace name, if any mapped.
        """

        data = representation.get("data", {}).get("colorspaceData", {})
        if not data:
            return

        ocio_colorspace = data["colorspace"]
        if not ocio_colorspace:
            return

        resolve_colorspace = get_remapped_colorspace_to_native(
            ocio_colorspace_name=ocio_colorspace,
            host_name="resolve",
            imageio_host_settings=self._host_imageio_settings
        )
        if resolve_colorspace:
            return resolve_colorspace
        else:
            self.log.warning(
                f"No mapping from OCIO colorspace '{ocio_colorspace}' "
                "found to a Resolve colorspace. "
                "Ignoring colorspace."
            )
