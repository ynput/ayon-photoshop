"""
Requires:
    - (ayon-core) CollectContextEntities
    context -> frameStart
    context -> frameEnd
    context -> fps

Provides:
    instance     -> family ("review")
"""

import pyblish.api


class CollectReviewData(pyblish.api.InstancePlugin):
    """Adds data needed for review."""

    label = "Collect Review data"
    hosts = ["photoshop"]
    # TODO lower order when 'CollectContextEntities' lowers order
    # order = pyblish.api.CollectorOrder - 0.4
    order = pyblish.api.CollectorOrder - 0.09
    settings_category = "photoshop"
    families = ["review"]

    def process(self, instance):
        context = instance.context
        instance.data["frameStart"] = context.data["frameStart"]
        instance.data["frameEnd"] = context.data["frameEnd"]
        instance.data["fps"] = context.data["fps"]
