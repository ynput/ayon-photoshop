from pathlib import Path
from ayon_core.pipeline import publish
from ayon_core.pipeline.publish import get_instance_staging_dir
from ayon_photoshop import api as photoshop


class ExtractLayers(publish.Extractor):
    """Export layers within the instance layerset to a PSD file.
    
    Layersets can be merged to reduce the number of layers in the output file.
    """

    label = "Extract Layers"
    order = publish.Extractor.order  # Must be after ExtractImage
    hosts = ["photoshop"]
    families = ["image"]
    merge_layersets = False

    def process(self, instance):
        ps_stub = photoshop.stub()

        # Duplicate the document to the staging directory
        filepath = Path(
            get_instance_staging_dir(instance),
            ps_stub.get_active_document_name()
        )
        self.log.info(f"Duplicating document to staging directory: {filepath}")
        with ps_stub.duplicate_document(
            filepath
        ):
            # Merge all layersets within the instance set
            if self.merge_layersets:
                self.log.info("Merging all layersets within instance set...")
                ps_stub.merge_all_layersets(
                    parent_set=instance.data.get("layer").id
                )

            # Dissolve instance layerset
            self.log.info("Dissolving instance layerset...")
            ps_stub.dissolve_layerset(
                instance.data.get("layer").id
            )

        instance.data["stagingDir"] = filepath.parent
        representations = instance.data.setdefault("representations", [])
        representations.append(
            {
                "name": "psd",
                "ext": "psd",
                "files": filepath.name,
                "stagingDir": filepath.parent,
            }
        )
