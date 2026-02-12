import os
import re
import pyblish.api

from ayon_photoshop import api, PHOTOSHOP_ADDON_ROOT

from ayon_core.pipeline import PublishError


class CollectExtensionVersion(pyblish.api.ContextPlugin):
    """ Pulls and compares version of installed extension.

        It is recommended to use same extension as in provided Openpype code.

        Please use Anastasiy’s Extension Manager or ZXPInstaller to update
        extension in case of an error.

        You can locate extension.zxp in your installed Openpype code in
        `repos/avalon-core/avalon/photoshop`
    """
    # This technically should be a validator, but other collectors might be
    # impacted with usage of obsolete extension, so collector that runs first
    # was chosen
    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect extension version"
    hosts = ["photoshop"]

    optional = True
    active = True

    def process(self, context):
        installed_version = api.stub().get_extension_version()

        if not installed_version:
            raise PublishError("Unknown version, probably old extension")

        manifest_url = os.path.join(
            PHOTOSHOP_ADDON_ROOT, "api", "extensions", "CSXS", "manifest.xml"
        )
        if not os.path.exists(manifest_url):
            self.log.debug("Unable to locate extension manifest, not checking")
            return

        with open(manifest_url) as fp:
            content = fp.read()

        found = re.findall(
            r'(ExtensionBundleVersion=")([0-9\.]+)(")',
            content
        )
        expected_version = None
        if found:
            expected_version = found[0][1]

        if expected_version != installed_version:
            msg = (
                f"Expected version '{expected_version}'"
                f" found '{installed_version}'\n"
                "Please update your installed extension, it might not work "
                "properly."
            )
            raise PublishError(msg)
