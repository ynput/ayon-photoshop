from ayon_photoshop.lib import PSAutoCreator


class WorkfileCreator(PSAutoCreator):
    identifier = "workfile"
    product_base_type = "workfile"
    product_type = product_base_type
    default_variant = "Main"

    def get_detail_description(self):
        return """Auto creator for workfile.

        It is expected that each publish will also publish its source workfile
        for safekeeping. This creator triggers automatically without need for
        an artist to remember and trigger it explicitly.

        Workfile instance could be disabled if it is not required to publish
        workfile. (Instance shouldn't be deleted though as it will be recreated
        in next publish automatically).
        """
