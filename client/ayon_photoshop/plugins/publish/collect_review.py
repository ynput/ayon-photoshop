"""

Provides:
    instance     -> families ("review")
"""

import pyblish.api


class CollectReview(pyblish.api.ContextPlugin):
    """Adds review to families for instances marked to be reviewable.
    """

    label = "Collect Review"
    hosts = ["photoshop"]
    order = pyblish.api.CollectorOrder - 0.45
    settings_category = "photoshop"

    def process(self, context):
        for instance in context:
            creator_attributes = instance.data.get("creator_attributes", {})
            # Add 'review' family if is instance marked for review
            if (
                creator_attributes.get("mark_for_review")
                and "review" not in instance.data["families"]
            ):
                instance.data["families"].append("review")
