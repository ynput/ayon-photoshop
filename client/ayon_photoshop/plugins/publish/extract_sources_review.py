import os
import shutil
from PIL import Image

from ayon_core.pipeline import publish
from ayon_photoshop import api as photoshop


class ExtractSourcesReview(publish.Extractor):
    """
        Produce a flattened or sequence image files from all 'image' instances.

        If no 'image' instance is created, it produces flattened image from
        all visible layers.

        It can also create separate reviews per `image` instance if necessary.
        (toggle on an instance in Publisher UI).

        'review' family could be used in other steps as a reference, as it
        contains flattened image by default. (Eg. artist could load this
        review as a single item and see full image. In most cases 'image'
        product type is separated by layers to better usage in animation
        or comp.)
    """

    label = "Extract Sources for Review"
    hosts = ["photoshop"]
    families = ["review"]
    settings_category = "photoshop"
    order = publish.Extractor.order - 0.28

    # Extract Options
    make_image_sequence = None

    def process(self, instance):
        staging_dir = self.staging_dir(instance)
        self.log.info("Outputting image to {}".format(staging_dir))

        stub = photoshop.stub()
        self.output_seq_filename = os.path.splitext(
            stub.get_active_document_name())[0] + ".%04d.jpg"

        layers = self._get_layers_from_image_instances(instance)
        self.log.info("Layers image instance found: {}".format(layers))

        additional_repre = {
            "name": "jpg",
            "ext": "jpg",
            "output_name": "jpg_jpg",
            "frameStart": instance.data["frameStart"],
            "frameEnd": instance.data["frameEnd"],
            "fps": instance.data["fps"],
            "stagingDir": staging_dir,
            "tags": ["review"],
        }

        if instance.data["productType"] == "image":
            self._attach_review_tag(instance)
        elif self.make_image_sequence and len(layers) > 1:
            self.log.debug("Extract layers to image sequence.")
            img_list = self._save_sequence_images(staging_dir, layers)

            instance.data["frameEnd"] = instance.data["frameStart"] + len(img_list) - 1

            additional_repre["files"] = img_list
            instance.data["representations"].append(additional_repre)

        else:
            self.log.debug("Extract layers to flatten image.")
            review_source_path = self._save_flatten_image(
                staging_dir,
                layers
            )
            additional_repre["files"] = os.path.basename(review_source_path)
            # just intermediate repre to create a review from
            additional_repre["tags"].append("delete")
            instance.data["representations"].append(additional_repre)

        instance.data["stagingDir"] = staging_dir

        self.log.info(f"Extracted {instance} to {staging_dir}")

    def _attach_review_tag(self, instance):
        """Searches for repre for which jpg review should be created.

        "jpg" representation is preferred.

        """
        jpg_source_repre = None
        for repre in instance.data["representations"]:
            if repre["name"] == "jpg":
                jpg_source_repre = repre
                repre["tags"].append("review")
                break

        if not jpg_source_repre:
            repre = instance.data["representations"][0]
            repre["tags"].append("review")

    def _get_layers_from_image_instances(self, instance):
        """Collect all layers from image instance(s)

        If `instance` is `image` it returns just layers out of it to create
        separate review per instance.

        If `instance` is (most likely) `review`, it collects all layers from
        published instances to create one review from all of them.

        Returns:
            (list) of PSItem
        """
        layers = []
        # creating review for existing 'image' instance
        if (
            instance.data["productType"] == "image"
            and instance.data.get("layer")
        ):
            layers.append(instance.data["layer"])
            return layers

        # collect all layers from published image instances
        for image_instance in instance.context:
            if image_instance.data["productType"] != "image":
                continue
            if not image_instance.data.get("layer"):
                # dummy instance for flatten image
                continue
            layers.append(image_instance.data.get("layer"))

        return sorted(layers)

    def _save_flatten_image(self, staging_dir, layers):
        """Creates flat image from 'layers' into 'staging_dir'.

        Returns:
            (str): path to new image
        """
        img_filename = self.output_seq_filename % 0
        output_image_path = os.path.join(staging_dir, img_filename)
        stub = photoshop.stub()

        with photoshop.maintained_visibility():
            self.log.info("Extracting {}".format(layers))
            if layers:
                stub.hide_all_others_layers(layers)

            stub.saveAs(output_image_path, 'jpg', True)

        return output_image_path

    def _save_sequence_images(self, staging_dir, layers):
        """Creates separate images from 'layers' into 'staging_dir'.

        `layers` are actually groups matching instances.

        Used as source for multi frames .mov to review at once.
        Returns:
            (list): paths to new images
        """
        stub = photoshop.stub()

        list_img_filename = []
        with photoshop.maintained_visibility():
            for i, layer in enumerate(layers):
                self.log.info("Extracting {}".format(layer))

                img_filename = self.output_seq_filename % i
                output_image_path = os.path.join(staging_dir, img_filename)
                list_img_filename.append(img_filename)

                with photoshop.maintained_visibility():
                    stub.hide_all_others_layers([layer])
                    stub.saveAs(output_image_path, 'jpg', True)

        return list_img_filename
