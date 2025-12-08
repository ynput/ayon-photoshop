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
        stub = photoshop.stub()
        hidden_layer_ids = set()

        all_layers = stub.get_layers()
        for layer in all_layers:
            if not layer.visible:
                hidden_layer_ids.add(layer.id)
        stub.hide_all_others_layers_ids([], layers=all_layers)

        with photoshop.maintained_selection():
            with photoshop.maintained_visibility(layers=all_layers):
                for instance in context:
                    if instance.data["productType"] not in self.families:
                        continue

                    staging_dir = self.staging_dir(instance)
                    self.log.info("Outputting image to {}".format(staging_dir))

                    # Perform extraction
                    files = {}
                    ids = set()
                    # real layers and groups
                    members = instance.data("members")
                    if members:
                        ids.update(set([int(member) for member in members]))
                    # virtual groups collected by color coding or auto_image
                    add_ids = instance.data.pop("ids", None)
                    if add_ids:
                        ids.update(set(add_ids))
                    extract_ids = set([ll.id for ll in stub.
                                      get_layers_in_layers_ids(ids, all_layers)
                                       if ll.id not in hidden_layer_ids])

                    for extracted_id in extract_ids:
                        stub.set_visible(extracted_id, True)

                    file_basename, workfile_extension = os.path.splitext(
                        stub.get_active_document_name()
                    )
                    workfile_extension = workfile_extension.strip(".")

                    for extension in self.formats:
                        _filename = "{}.{}".format(file_basename,
                                                    extension)
                        files[extension] = _filename

                        full_filename = os.path.join(staging_dir,
                                                     _filename)
                        if extension == "tga":
                            self._save_image_to_targa(
                                stub, full_filename, extension, workfile_extension
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
                        # inject colorspace data
                        self.set_representation_colorspace(
                            repre, context,
                            colorspace=ayon_colorspace
                        )
                        representations.append(repre)
                    instance.data["representations"] = representations
                    instance.data["stagingDir"] = staging_dir

                    self.log.info(f"Extracted {instance} to {staging_dir}")

                    for extracted_id in extract_ids:
                        stub.set_visible(extracted_id, False)

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
