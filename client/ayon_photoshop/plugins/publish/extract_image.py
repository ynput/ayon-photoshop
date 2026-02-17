import os

import pyblish.api
from ayon_core.pipeline import publish
from ayon_core.pipeline.colorspace import get_remapped_colorspace_from_native
from ayon_photoshop import api as photoshop


class ExtractImage(
    pyblish.api.ContextPlugin,
    publish.ColormanagedPyblishPluginMixin
):
    """Extract all layers (groups) marked for publish.

    Usually publishable instance is created as a wrapper of layer(s). For each
    publishable instance so many images as there is 'formats' is created.

    Logic tries to hide/unhide layers minimum times.

    Called once for all publishable instances.
    """

    order = publish.Extractor.order - 0.48
    label = "Extract Image"
    hosts = ["photoshop"]

    families = ["image", "background"]
    formats = ["png", "jpg", "tga"]
    settings_category = "photoshop"

    def process(self, context):
        # Filter instances
        filtered_instances = []
        for instance in context:
            product_base_type = instance.data.get("productBaseType")
            if not product_base_type:
                product_base_type = instance.data["productType"]
            if product_base_type in self.families:
                filtered_instances.append(instance)

        if not filtered_instances:
            return

        stub = photoshop.stub()
        all_layers = stub.get_layers()  # Fetch once, reuse for all instances
        native_colorspace = stub.get_color_profile_name()
        self.log.info(f"Document colorspace profile: {native_colorspace}")
        host_name = context.data["hostName"]
        project_settings = context.data["project_settings"]
        host_imageio_settings = project_settings["photoshop"]["imageio"]

        with photoshop.maintained_selection():
            for instance in filtered_instances:
                suffix = instance.data["name"]
                staging_dir = self.staging_dir(instance)
                self.log.info(f"Outputting image to {staging_dir}")

                # Get instance layer ID
                members = instance.data("members")
                if not members:
                    continue
                instance_id = int(members[0])

                # Context manager handles all visibility: show instance path,
                # hide siblings, restore original state on exit
                with photoshop.isolated_layers_visibility(stub, instance_id, all_layers):
                    # Perform extraction
                    files = {}
                    ids = set()
                    # real layers and groups
                    if members:
                        ids.update(int(member) for member in members)
                    # virtual groups collected by color coding or auto_image
                    add_ids = instance.data.pop("ids", None)
                    if add_ids:
                        ids.update(set(add_ids))

                    extract_ids = {
                        ll.id
                        for ll in stub.get_layers_in_layers_ids(
                            ids, all_layers
                        )
                        if ll.id not in hidden_layer_ids
                    }

                    for extracted_id in extract_ids:
                        stub.set_visible(extracted_id, True)

                    file_basename, workfile_extension = os.path.splitext(
                        stub.get_active_document_name()
                    )
                    workfile_extension = workfile_extension.strip(".")

                    for extension in self.formats:
                        repre_filename = f"{file_basename}_{suffix}.{extension}"
                        files[extension] = repre_filename

                        full_filename = os.path.join(
                            staging_dir, repre_filename)
                        if extension == "tga":
                            self._save_image_to_targa(
                                stub,
                                full_filename,
                                extension,
                                workfile_extension
                            )
                        else:
                            stub.saveAs(full_filename, extension, True)
                        self.log.info(f"Extracted: {extension}")

                    representations = []
                    for extension, filename in files.items():
                        repre = {
                            "name": extension,
                            "ext": extension,
                            "files": filename,
                            "stagingDir": staging_dir,
                            "tags": [],
                        }
                        ayon_colorspace = get_remapped_colorspace_from_native(
                            native_colorspace,
                            host_name,
                            host_imageio_settings,
                        )
                        self.log.debug(f"ayon_colorspace: {ayon_colorspace}")
                        # inject colorspace data
                        self.set_representation_colorspace(
                            repre, context,
                            colorspace=ayon_colorspace
                        )
                        self.log.debug(f"representation: {repre}")
                        representations.append(repre)
                    instance.data["representations"] = representations
                    instance.data["stagingDir"] = staging_dir

                    self.log.info(f"Extracted {instance} to {staging_dir}")

    def staging_dir(self, instance):
        """Provide a temporary directory in which to store extracted files

        Upon calling this method the staging directory is stored inside
        the instance.data['stagingDir']
        """

        from ayon_core.pipeline.publish import get_instance_staging_dir

        return get_instance_staging_dir(instance)


    def _save_image_to_targa(self, stub, full_filename, extension, workfile_extension):
        """Hacky way to save image in targa. Save the psd file
        in quiet mode with targa options first and then convert it into targa
        ***Caution to use it.

        Args:
            stub (RPC stub): stub to call method
            full_filename (str): full published filename
            extension (str): published extension
            workfile_extension (str): workfile extension
        """
        src_file = full_filename.replace(extension, workfile_extension)
        stub.saveAs(full_filename, extension, True)
        if os.path.exists(src_file):
            os.rename(src_file, full_filename)
