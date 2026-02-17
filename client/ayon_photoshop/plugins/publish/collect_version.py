"""
Requires:
    context -> version

Provides:
    instance -> version - incremented latest published workfile version

"""
import pyblish.api


class CollectVersion(pyblish.api.InstancePlugin):
    """Collect version for publishable instances.

    Used to synchronize version from workfile to all publishable instances:
        - image (manually created or color coded)
        - review
        - workfile

    Dev comment:
    Explicit collector created to control this from single place and not from
    3 different.

    Workfile set here explicitly as version might to be forced from latest + 1
    because of Webpublisher.
    (This plugin must run after CollectPublishedVersion!)
    """
    # TODO lower order when 'CollectPublishedVersion' lowers order
    # - Or move the logic to the very same plugin?
    # order = pyblish.api.CollectorOrder - 0.35
    order = pyblish.api.CollectorOrder - 0.07
    label = "Collect Version"

    hosts = ["photoshop"]
    families = ["image", "review", "workfile"]
    settings_category = "photoshop"

    def process(self, instance):
        workfile_version = instance.context.data["version"]
        self.log.debug(f"Applying version {workfile_version}")
        instance.data["version"] = workfile_version
